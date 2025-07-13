// Website and Page Types
export interface Website {
  id: string;
  name: string;
  description: string;
  domain?: string;
  subdomain: string;
  theme: string;
  favicon?: string;
  logo?: string;
  isPublished: boolean;
  createdAt: Date;
  updatedAt: Date;
  pages: Page[];
  settings: WebsiteSettings;
}

export interface Page {
  id: string;
  websiteId: string;
  title: string;
  slug: string;
  content: PageContent;
  metaTitle?: string;
  metaDescription?: string;
  isHomePage: boolean;
  isPublished: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface PageContent {
  sections: Section[];
  globalStyles: GlobalStyles;
}

export interface Section {
  id: string;
  type: SectionType;
  title?: string;
  content: SectionContent;
  styles: SectionStyles;
  order: number;
  isVisible: boolean;
}

export type SectionType = 
  | 'hero'
  | 'about'
  | 'services'
  | 'portfolio'
  | 'testimonials'
  | 'contact'
  | 'blog'
  | 'team'
  | 'pricing'
  | 'faq'
  | 'cta'
  | 'features'
  | 'stats'
  | 'gallery'
  | 'footer'
  | 'header'
  | 'custom';

export interface SectionContent {
  heading?: string;
  subheading?: string;
  description?: string;
  image?: string;
  images?: string[];
  buttons?: Button[];
  items?: ContentItem[];
  form?: FormField[];
  html?: string;
}

export interface Button {
  id: string;
  text: string;
  url: string;
  style: ButtonStyle;
  target?: '_blank' | '_self';
}

export type ButtonStyle = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link';

export interface ContentItem {
  id: string;
  title: string;
  description?: string;
  image?: string;
  link?: string;
  metadata?: Record<string, any>;
}

export interface FormField {
  id: string;
  type: 'text' | 'email' | 'tel' | 'textarea' | 'select' | 'checkbox' | 'radio';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
}

// Styling Types
export interface GlobalStyles {
  colors: ColorPalette;
  typography: Typography;
  spacing: Spacing;
  layout: Layout;
}

export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
  muted: string;
  border: string;
  success: string;
  warning: string;
  error: string;
}

export interface Typography {
  fontFamily: string;
  headingFontFamily?: string;
  baseFontSize: string;
  headingWeight: string;
  bodyWeight: string;
  lineHeight: string;
  headingLineHeight: string;
}

export interface Spacing {
  baseUnit: string;
  sectionPadding: string;
  containerMaxWidth: string;
}

export interface Layout {
  containerMaxWidth: string;
  sidebarWidth: string;
  headerHeight: string;
  footerHeight: string;
}

export interface SectionStyles {
  backgroundColor: string;
  textColor: string;
  padding: string;
  margin: string;
  borderRadius: string;
  boxShadow: string;
  border: string;
  customCSS?: string;
}

// Website Settings
export interface WebsiteSettings {
  seo: SEOSettings;
  integrations: IntegrationSettings;
  customCode: CustomCodeSettings;
  analytics: AnalyticsSettings;
}

export interface SEOSettings {
  title: string;
  description: string;
  keywords: string[];
  ogImage?: string;
  twitterCard?: string;
  canonicalUrl?: string;
  robots: string;
  sitemap: boolean;
}

export interface IntegrationSettings {
  googleAnalytics?: string;
  googleTagManager?: string;
  facebookPixel?: string;
  hotjar?: string;
  intercom?: string;
  mailchimp?: string;
  stripe?: string;
}

export interface CustomCodeSettings {
  headHTML?: string;
  bodyHTML?: string;
  css?: string;
  javascript?: string;
}

export interface AnalyticsSettings {
  enabled: boolean;
  provider: 'google' | 'plausible' | 'mixpanel' | 'custom';
  trackingId?: string;
  customScript?: string;
}

// Template Types
export interface Template {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  thumbnail: string;
  preview: string;
  isPremium: boolean;
  tags: string[];
  content: PageContent;
  createdAt: Date;
  updatedAt: Date;
}

export type TemplateCategory = 
  | 'business'
  | 'portfolio'
  | 'blog'
  | 'ecommerce'
  | 'landing'
  | 'restaurant'
  | 'agency'
  | 'creative'
  | 'health'
  | 'education'
  | 'nonprofit'
  | 'event'
  | 'real-estate'
  | 'technology'
  | 'finance';

// AI Generation Types
export interface AIGenerationRequest {
  type: 'website' | 'section' | 'content' | 'image';
  prompt: string;
  context?: AIGenerationContext;
  options?: AIGenerationOptions;
}

export interface AIGenerationContext {
  businessType?: string;
  industry?: string;
  targetAudience?: string;
  tone?: string;
  style?: string;
  existingContent?: string;
  websiteType?: string;
}

export interface AIGenerationOptions {
  includeImages?: boolean;
  wordCount?: number;
  sections?: SectionType[];
  colorScheme?: string;
  layout?: string;
  features?: string[];
}

export interface AIGenerationResponse {
  success: boolean;
  data?: any;
  error?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// User and Project Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  plan: UserPlan;
  createdAt: Date;
  updatedAt: Date;
}

export type UserPlan = 'free' | 'pro' | 'enterprise';

export interface Project {
  id: string;
  userId: string;
  name: string;
  description?: string;
  websites: Website[];
  createdAt: Date;
  updatedAt: Date;
}

// Form and Validation Types
export interface FormData {
  [key: string]: any;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: ValidationError[];
  message?: string;
}

// UI Component Types
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ThemeConfig {
  name: string;
  colors: ColorPalette;
  typography: Typography;
  spacing: Spacing;
  borderRadius: string;
  shadows: Record<string, string>;
}

// Editor Types
export interface EditorState {
  selectedSection?: string;
  selectedElement?: string;
  isPreviewMode: boolean;
  device: 'desktop' | 'tablet' | 'mobile';
  zoom: number;
  history: EditorHistory[];
  historyIndex: number;
}

export interface EditorHistory {
  id: string;
  action: string;
  timestamp: Date;
  state: any;
}

// Export and Deployment Types
export interface ExportOptions {
  format: 'html' | 'react' | 'vue' | 'angular';
  includeAssets: boolean;
  minify: boolean;
  responsive: boolean;
  seo: boolean;
}

export interface DeploymentOptions {
  provider: 'vercel' | 'netlify' | 'aws' | 'github-pages' | 'custom';
  domain?: string;
  subdomain?: string;
  buildCommand?: string;
  outputDirectory?: string;
  environmentVariables?: Record<string, string>;
}

export interface DeploymentStatus {
  id: string;
  status: 'pending' | 'building' | 'deployed' | 'failed';
  url?: string;
  error?: string;
  logs?: string[];
  startedAt: Date;
  completedAt?: Date;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  stack?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: any;
}