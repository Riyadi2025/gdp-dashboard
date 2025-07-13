import OpenAI from 'openai';
import { AIGenerationRequest, AIGenerationResponse, AIGenerationContext, SectionType } from '@/types';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export class OpenAIService {
  static async generateWebsite(prompt: string, context?: AIGenerationContext): Promise<AIGenerationResponse> {
    try {
      const systemPrompt = this.buildWebsiteSystemPrompt(context);
      const userPrompt = this.buildWebsiteUserPrompt(prompt, context);

      const response = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        functions: [{
          name: 'generate_website',
          description: 'Generate a complete website structure with content',
          parameters: {
            type: 'object',
            properties: {
              website: {
                type: 'object',
                properties: {
                  name: { type: 'string', description: 'Website name' },
                  description: { type: 'string', description: 'Website description' },
                  pages: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        title: { type: 'string' },
                        slug: { type: 'string' },
                        sections: {
                          type: 'array',
                          items: {
                            type: 'object',
                            properties: {
                              type: { type: 'string', enum: ['hero', 'about', 'services', 'portfolio', 'testimonials', 'contact', 'blog', 'team', 'pricing', 'faq', 'cta', 'features', 'stats', 'gallery', 'footer', 'header'] },
                              content: {
                                type: 'object',
                                properties: {
                                  heading: { type: 'string' },
                                  subheading: { type: 'string' },
                                  description: { type: 'string' },
                                  image: { type: 'string' },
                                  images: { type: 'array', items: { type: 'string' } },
                                  buttons: {
                                    type: 'array',
                                    items: {
                                      type: 'object',
                                      properties: {
                                        text: { type: 'string' },
                                        url: { type: 'string' },
                                        style: { type: 'string', enum: ['primary', 'secondary', 'outline', 'ghost', 'link'] }
                                      }
                                    }
                                  },
                                  items: {
                                    type: 'array',
                                    items: {
                                      type: 'object',
                                      properties: {
                                        title: { type: 'string' },
                                        description: { type: 'string' },
                                        image: { type: 'string' },
                                        link: { type: 'string' }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  theme: {
                    type: 'object',
                    properties: {
                      colors: {
                        type: 'object',
                        properties: {
                          primary: { type: 'string' },
                          secondary: { type: 'string' },
                          accent: { type: 'string' },
                          background: { type: 'string' },
                          text: { type: 'string' }
                        }
                      },
                      typography: {
                        type: 'object',
                        properties: {
                          fontFamily: { type: 'string' },
                          headingFontFamily: { type: 'string' }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }],
        function_call: { name: 'generate_website' },
        temperature: 0.7,
        max_tokens: 4000,
      });

      const functionCall = response.choices[0].message.function_call;
      if (functionCall && functionCall.arguments) {
        const websiteData = JSON.parse(functionCall.arguments);
        return {
          success: true,
          data: websiteData.website,
          usage: {
            promptTokens: response.usage?.prompt_tokens || 0,
            completionTokens: response.usage?.completion_tokens || 0,
            totalTokens: response.usage?.total_tokens || 0,
          }
        };
      }

      throw new Error('No function call response received');
    } catch (error) {
      console.error('OpenAI website generation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  static async generateSection(sectionType: SectionType, prompt: string, context?: AIGenerationContext): Promise<AIGenerationResponse> {
    try {
      const systemPrompt = this.buildSectionSystemPrompt(sectionType, context);
      const userPrompt = `Generate a ${sectionType} section with the following requirements: ${prompt}`;

      const response = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        functions: [{
          name: 'generate_section',
          description: `Generate a ${sectionType} section with content`,
          parameters: {
            type: 'object',
            properties: {
              section: {
                type: 'object',
                properties: {
                  type: { type: 'string', enum: [sectionType] },
                  content: {
                    type: 'object',
                    properties: {
                      heading: { type: 'string' },
                      subheading: { type: 'string' },
                      description: { type: 'string' },
                      image: { type: 'string' },
                      images: { type: 'array', items: { type: 'string' } },
                      buttons: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            text: { type: 'string' },
                            url: { type: 'string' },
                            style: { type: 'string', enum: ['primary', 'secondary', 'outline', 'ghost', 'link'] }
                          }
                        }
                      },
                      items: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            title: { type: 'string' },
                            description: { type: 'string' },
                            image: { type: 'string' },
                            link: { type: 'string' }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }],
        function_call: { name: 'generate_section' },
        temperature: 0.7,
        max_tokens: 2000,
      });

      const functionCall = response.choices[0].message.function_call;
      if (functionCall && functionCall.arguments) {
        const sectionData = JSON.parse(functionCall.arguments);
        return {
          success: true,
          data: sectionData.section,
          usage: {
            promptTokens: response.usage?.prompt_tokens || 0,
            completionTokens: response.usage?.completion_tokens || 0,
            totalTokens: response.usage?.total_tokens || 0,
          }
        };
      }

      throw new Error('No function call response received');
    } catch (error) {
      console.error('OpenAI section generation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  static async generateContent(prompt: string, context?: AIGenerationContext): Promise<AIGenerationResponse> {
    try {
      const systemPrompt = this.buildContentSystemPrompt(context);

      const response = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 2000,
      });

      const content = response.choices[0].message.content;
      if (content) {
        return {
          success: true,
          data: { content },
          usage: {
            promptTokens: response.usage?.prompt_tokens || 0,
            completionTokens: response.usage?.completion_tokens || 0,
            totalTokens: response.usage?.total_tokens || 0,
          }
        };
      }

      throw new Error('No content generated');
    } catch (error) {
      console.error('OpenAI content generation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  static async generateImage(prompt: string, size: '256x256' | '512x512' | '1024x1024' = '1024x1024'): Promise<AIGenerationResponse> {
    try {
      const response = await openai.images.generate({
        model: 'dall-e-3',
        prompt: prompt,
        size: size,
        quality: 'standard',
        n: 1,
      });

      const imageUrl = response.data[0]?.url;
      if (imageUrl) {
        return {
          success: true,
          data: { imageUrl, prompt }
        };
      }

      throw new Error('No image generated');
    } catch (error) {
      console.error('OpenAI image generation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  private static buildWebsiteSystemPrompt(context?: AIGenerationContext): string {
    const basePrompt = `You are an expert web designer and content creator. Generate a complete, professional website structure with compelling content.

Guidelines:
- Create engaging, conversion-focused content
- Use modern, clean design principles
- Include relevant sections based on business type
- Generate specific, actionable content (not placeholder text)
- Ensure content is SEO-friendly and user-focused
- Use professional tone unless specified otherwise
- Include appropriate call-to-action buttons
- Make content scannable with good hierarchy`;

    if (context) {
      return `${basePrompt}

Context:
${context.businessType ? `Business Type: ${context.businessType}` : ''}
${context.industry ? `Industry: ${context.industry}` : ''}
${context.targetAudience ? `Target Audience: ${context.targetAudience}` : ''}
${context.tone ? `Tone: ${context.tone}` : ''}
${context.style ? `Style: ${context.style}` : ''}
${context.websiteType ? `Website Type: ${context.websiteType}` : ''}`;
    }

    return basePrompt;
  }

  private static buildWebsiteUserPrompt(prompt: string, context?: AIGenerationContext): string {
    return `Create a professional website for: ${prompt}

Requirements:
- Generate a complete homepage with multiple sections
- Include hero, about, services/features, and contact sections at minimum
- Add testimonials, portfolio, or other relevant sections based on business type
- Create compelling headlines and descriptions
- Include appropriate call-to-action buttons
- Generate a cohesive color scheme and typography
- Make content specific and valuable (avoid generic placeholder text)
- Ensure mobile-responsive design considerations

${context?.features ? `Special features to include: ${context.features.join(', ')}` : ''}`;
  }

  private static buildSectionSystemPrompt(sectionType: SectionType, context?: AIGenerationContext): string {
    const sectionPrompts = {
      hero: 'Create a compelling hero section with a strong headline, subheadline, and clear call-to-action',
      about: 'Write an engaging about section that builds trust and credibility',
      services: 'Generate a services section with clear value propositions',
      portfolio: 'Create a portfolio section showcasing work and achievements',
      testimonials: 'Write authentic testimonials that build social proof',
      contact: 'Create a contact section with clear contact information and form',
      blog: 'Generate a blog section with relevant article previews',
      team: 'Create a team section highlighting key team members',
      pricing: 'Generate a pricing section with clear plans and benefits',
      faq: 'Create an FAQ section addressing common questions',
      cta: 'Write a compelling call-to-action section',
      features: 'Generate a features section highlighting key benefits',
      stats: 'Create a statistics section with impressive numbers',
      gallery: 'Generate a gallery section with image descriptions',
      footer: 'Create a comprehensive footer with all necessary links',
      header: 'Generate a header section with navigation',
      custom: 'Create a custom section based on specific requirements'
    };

    const basePrompt = `You are an expert web designer creating a ${sectionType} section. ${sectionPrompts[sectionType] || sectionPrompts.custom}

Guidelines:
- Create specific, actionable content
- Use professional, engaging language
- Include relevant imagery suggestions
- Ensure content is conversion-focused
- Make content scannable and well-structured`;

    if (context) {
      return `${basePrompt}

Context:
${context.businessType ? `Business Type: ${context.businessType}` : ''}
${context.industry ? `Industry: ${context.industry}` : ''}
${context.targetAudience ? `Target Audience: ${context.targetAudience}` : ''}
${context.tone ? `Tone: ${context.tone}` : ''}`;
    }

    return basePrompt;
  }

  private static buildContentSystemPrompt(context?: AIGenerationContext): string {
    const basePrompt = `You are an expert content writer creating engaging, professional web content.

Guidelines:
- Write clear, compelling content
- Use appropriate tone and style
- Include relevant keywords naturally
- Make content scannable and well-structured
- Focus on user benefits and value
- Include calls-to-action where appropriate`;

    if (context) {
      return `${basePrompt}

Context:
${context.businessType ? `Business Type: ${context.businessType}` : ''}
${context.industry ? `Industry: ${context.industry}` : ''}
${context.targetAudience ? `Target Audience: ${context.targetAudience}` : ''}
${context.tone ? `Tone: ${context.tone}` : ''}`;
    }

    return basePrompt;
  }
}

export default OpenAIService;