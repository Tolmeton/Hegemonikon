import { readFile } from "node:fs/promises";

const promptFile = process.env.PROMPT_FILE || "/input/prompt.md";
const model = process.env.GEMINI_MODEL || "gemini-3-flash-preview";
const apiKey = process.env.GOOGLE_API_KEY;

if (!apiKey) {
  console.error("GOOGLE_API_KEY is missing.");
  process.exit(2);
}

const source = await readFile(promptFile, "utf8");
const match = source.match(/^```text\n([\s\S]*?)\n```/m);
const prompt = match ? match[1] : source;

const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`;

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-goog-api-key": apiKey,
  },
  body: JSON.stringify({
    contents: [
      {
        role: "user",
        parts: [{ text: prompt }],
      },
    ],
    generationConfig: {
      temperature: 0.2,
      maxOutputTokens: 12000,
    },
  }),
});

const text = await response.text();

if (!response.ok) {
  console.error(`Gemini API error: HTTP ${response.status}`);
  try {
    const parsed = JSON.parse(text);
    console.error(JSON.stringify(parsed, null, 2));
  } catch {
    console.error(text);
  }
  process.exit(1);
}

const parsed = JSON.parse(text);
const parts = parsed?.candidates?.[0]?.content?.parts || [];
const output = parts.map((part) => part.text || "").join("");

if (!output.trim()) {
  console.error("Gemini API returned no text output.");
  console.error(JSON.stringify(parsed, null, 2));
  process.exit(1);
}

process.stdout.write(output);
if (!output.endsWith("\n")) {
  process.stdout.write("\n");
}
