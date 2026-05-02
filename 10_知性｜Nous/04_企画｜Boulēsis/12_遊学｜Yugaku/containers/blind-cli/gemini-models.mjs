const apiKey = process.env.GOOGLE_API_KEY;

if (!apiKey) {
  console.error("GOOGLE_API_KEY is missing.");
  process.exit(2);
}

const endpoint = "https://generativelanguage.googleapis.com/v1beta/models";
const response = await fetch(endpoint, {
  headers: {
    "x-goog-api-key": apiKey,
  },
});

const text = await response.text();

if (!response.ok) {
  console.error(`Gemini models API error: HTTP ${response.status}`);
  try {
    const parsed = JSON.parse(text);
    console.error(JSON.stringify(parsed, null, 2));
  } catch {
    console.error(text);
  }
  process.exit(1);
}

const parsed = JSON.parse(text);
for (const model of parsed.models || []) {
  const name = String(model.name || "").replace(/^models\//, "");
  const methods = Array.isArray(model.supportedGenerationMethods)
    ? model.supportedGenerationMethods.join(",")
    : "";
  if (methods.includes("generateContent")) {
    console.log(name);
  }
}
