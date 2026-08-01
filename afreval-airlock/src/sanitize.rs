use regex::Regex;

pub fn mask(text: &str) -> String {
    let email = Regex::new(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}").unwrap();
    let phone = Regex::new(r"(\+?\d[\d\s\-()]{7,}\d)").unwrap();
    let national_id = Regex::new(r"\b\d{6,12}\b").unwrap();
    let masked = email.replace_all(text, "[EMAIL]").to_string();
    let masked = phone.replace_all(&masked, "[PHONE]").to_string();
    national_id.replace_all(&masked, "[ID]").to_string()
}

pub fn sanitize(bytes: &[u8], max_bytes: usize) -> Result<Vec<u8>, String> {
    if bytes.len() > max_bytes {
        return Err(format!("output exceeds max {} bytes", max_bytes));
    }
    let text = std::str::from_utf8(bytes).map_err(|_| "output is not valid UTF-8")?;
    Ok(mask(text).into_bytes())
}
