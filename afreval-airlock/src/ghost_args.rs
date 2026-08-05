
use crate::{ParamType, Policy, ToolSchema};

use serde::de::{self, MapAccess, Visitor};
use serde::Deserialize;

/// Deserializes a JSON object, rejecting duplicate keys (last-wins would
/// silently swallow an injected value — the seam-2 "dup key last wins" finding
/// 2026-08-05). RFC 8259 says duplicate keys are undefined behavior; we deny.
pub struct StrictArgs(pub serde_json::Value);

impl<'de> Deserialize<'de> for StrictArgs {
    fn deserialize<D>(d: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = StrictArgs;
            fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                f.write_str("a JSON object with unique keys")
            }
            fn visit_map<A>(self, mut map: A) -> Result<StrictArgs, A::Error>
            where
                A: MapAccess<'de>,
            {
                let mut seen: Vec<String> = Vec::new();
                let mut obj = serde_json::Map::new();
                while let Some(key) = map.next_key::<String>()? {
                    if seen.contains(&key) {
                        return Err(de::Error::custom(format!("duplicate key '{key}' in arguments")));
                    }
                    seen.push(key.clone());
                    let value = map.next_value::<serde_json::Value>()?;
                    obj.insert(key, value);
                }
                Ok(StrictArgs(serde_json::Value::Object(obj)))
            }
        }
        d.deserialize_map(V)
    }
}

pub struct Stripped {
    pub arguments: serde_json::Value,
    pub removed: Vec<String>,
}

fn type_matches(kind: ParamType, v: &serde_json::Value) -> bool {
    match kind {
        ParamType::String => v.is_string(),
        ParamType::Integer => v.is_i64() || v.is_u64(),
        ParamType::Number => v.is_number(),
        ParamType::Boolean => v.is_boolean(),
    }
}

pub fn validate_and_strip(tool: &str, arguments: &serde_json::Value, policy: &Policy) -> Result<Stripped, String> {
    let schema: &ToolSchema = policy
        .schemas
        .get(tool)
        .ok_or_else(|| format!("no schema declared for tool '{tool}'"))?;

    let obj = arguments
        .as_object()
        .ok_or_else(|| format!("arguments for '{tool}' must be a JSON object"))?;

    let mut cleaned = serde_json::Map::new();
    let mut removed = Vec::new();
    for (name, value) in obj {
        match schema.params.get(name) {
            Some(ps) => {
                if !type_matches(ps.kind, value) {
                    return Err(format!("param '{name}' wrong type (expected {:?})", ps.kind));
                }
                cleaned.insert(name.clone(), value.clone());
            }
            None => removed.push(name.clone()),
        }
    }
    for (name, ps) in &schema.params {
        if ps.required && !cleaned.contains_key(name) {
            return Err(format!("required param '{name}' missing"));
        }
    }
    Ok(Stripped {
        arguments: serde_json::Value::Object(cleaned),
        removed,
    })
}
