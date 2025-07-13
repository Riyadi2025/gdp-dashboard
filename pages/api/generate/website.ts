import { NextApiRequest, NextApiResponse } from 'next';
import { OpenAIService } from '../../../lib/openai';
import { AIGenerationContext } from '../../../types';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  try {
    const { prompt, context } = req.body as {
      prompt: string;
      context?: AIGenerationContext;
    };

    if (!prompt) {
      return res.status(400).json({ 
        success: false, 
        error: 'Prompt is required' 
      });
    }

    const result = await OpenAIService.generateWebsite(prompt, context);
    
    return res.status(200).json(result);
  } catch (error) {
    console.error('Website generation error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to generate website'
    });
  }
}