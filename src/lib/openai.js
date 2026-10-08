import { config } from '../config.js';
import OpenAI from 'openai';

export async function summarizeVehicle(vin, decodedData, customPrompt = '') {
  if (!config.openAIKey) {
    return {
      enabled: false,
      summary: 'OpenAI is not configured. Add OPENAI_API_KEY to enable AI summaries.'
    };
  }

  const vehicleData = Array.isArray(decodedData?.results) ? decodedData.results : [];

  const systemPrompt = `You are a vehicle analyst. Summarize vehicle details in plain language and avoid guesses if information is missing.`;
  const userPrompt = customPrompt || 'Provide a concise summary of this vehicle.';

  const client = new OpenAI({ apiKey: config.openAIKey });

  const completion = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0.2,
    messages: [
      { role: 'system', content: systemPrompt },
      {
        role: 'user',
        content: `${userPrompt}\n\nVIN: ${vin}\nVehicle data:\n${JSON.stringify(vehicleData, null, 2)}`
      }
    ]
  });

  const summary = completion.choices?.[0]?.message?.content?.trim() || 'No summary returned.';

  return {
    enabled: true,
    summary
  };
}
