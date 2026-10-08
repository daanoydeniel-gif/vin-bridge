import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: Number(process.env.PORT || 3000),
  openAIKey: process.env.OPENAI_API_KEY || '',
  nhtsaBaseUrl: process.env.NHTSA_BASE_URL || 'https://vpic.nhtsa.dot.gov/api/vehicles/'
};
