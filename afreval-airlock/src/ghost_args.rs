
use crate::{ParamType, Policy, ToolSchema};

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
