import { v4 as uuidv4 } from 'uuid';
import { Website, Page, Section, SectionType, ColorPalette, Typography } from '@/types';

// ID Generation
export const generateId = (): string => {
  return uuidv4();
};

// String Utilities
export const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

export const truncate = (text: string, length: number): string => {
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

export const capitalize = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
};

// Color Utilities
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
};

export const rgbToHex = (r: number, g: number, b: number): string => {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
};

export const lightenColor = (color: string, percent: number): string => {
  const rgb = hexToRgb(color);
  if (!rgb) return color;
  
  const { r, g, b } = rgb;
  const newR = Math.round(r + (255 - r) * percent / 100);
  const newG = Math.round(g + (255 - g) * percent / 100);
  const newB = Math.round(b + (255 - b) * percent / 100);
  
  return rgbToHex(newR, newG, newB);
};

export const darkenColor = (color: string, percent: number): string => {
  const rgb = hexToRgb(color);
  if (!rgb) return color;
  
  const { r, g, b } = rgb;
  const newR = Math.round(r * (100 - percent) / 100);
  const newG = Math.round(g * (100 - percent) / 100);
  const newB = Math.round(b * (100 - percent) / 100);
  
  return rgbToHex(newR, newG, newB);
};

// Validation Utilities
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidHexColor = (color: string): boolean => {
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
  return hexRegex.test(color);
};

// Array Utilities
export const shuffle = <T>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

// Object Utilities
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

export const omit = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => delete result[key]);
  return result;
};

export const pick = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

// Website Utilities
export const createDefaultWebsite = (name: string, description: string): Partial<Website> => {
  const id = generateId();
  return {
    id,
    name,
    description,
    subdomain: slugify(name),
    theme: 'default',
    isPublished: false,
    createdAt: new Date(),
    updatedAt: new Date(),
    pages: [],
    settings: {
      seo: {
        title: name,
        description,
        keywords: [],
        robots: 'index, follow',
        sitemap: true,
      },
      integrations: {},
      customCode: {},
      analytics: {
        enabled: false,
        provider: 'google',
      },
    },
  };
};

export const createDefaultPage = (websiteId: string, title: string, isHomePage: boolean = false): Page => {
  const id = generateId();
  return {
    id,
    websiteId,
    title,
    slug: isHomePage ? '' : slugify(title),
    content: {
      sections: [],
      globalStyles: getDefaultGlobalStyles(),
    },
    isHomePage,
    isPublished: false,
    createdAt: new Date(),
    updatedAt: new Date(),
  };
};

export const createDefaultSection = (type: SectionType, order: number): Section => {
  const id = generateId();
  return {
    id,
    type,
    content: {},
    styles: getDefaultSectionStyles(),
    order,
    isVisible: true,
  };
};

export const getDefaultGlobalStyles = () => ({
  colors: {
    primary: '#3b82f6',
    secondary: '#64748b',
    accent: '#06b6d4',
    background: '#ffffff',
    text: '#1f2937',
    muted: '#6b7280',
    border: '#e5e7eb',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    headingFontFamily: 'Inter, sans-serif',
    baseFontSize: '16px',
    headingWeight: '600',
    bodyWeight: '400',
    lineHeight: '1.6',
    headingLineHeight: '1.3',
  },
  spacing: {
    baseUnit: '1rem',
    sectionPadding: '4rem',
    containerMaxWidth: '1200px',
  },
  layout: {
    containerMaxWidth: '1200px',
    sidebarWidth: '300px',
    headerHeight: '80px',
    footerHeight: '200px',
  },
});

export const getDefaultSectionStyles = () => ({
  backgroundColor: 'transparent',
  textColor: 'inherit',
  padding: '2rem',
  margin: '0',
  borderRadius: '0',
  boxShadow: 'none',
  border: 'none',
});

// Theme Utilities
export const generateColorPalette = (primaryColor: string): ColorPalette => {
  return {
    primary: primaryColor,
    secondary: darkenColor(primaryColor, 20),
    accent: lightenColor(primaryColor, 30),
    background: '#ffffff',
    text: '#1f2937',
    muted: '#6b7280',
    border: '#e5e7eb',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
  };
};

export const getFontPairings = (): Typography[] => {
  return [
    {
      fontFamily: 'Inter, sans-serif',
      headingFontFamily: 'Inter, sans-serif',
      baseFontSize: '16px',
      headingWeight: '600',
      bodyWeight: '400',
      lineHeight: '1.6',
      headingLineHeight: '1.3',
    },
    {
      fontFamily: 'Roboto, sans-serif',
      headingFontFamily: 'Roboto Slab, serif',
      baseFontSize: '16px',
      headingWeight: '700',
      bodyWeight: '400',
      lineHeight: '1.6',
      headingLineHeight: '1.3',
    },
    {
      fontFamily: 'Open Sans, sans-serif',
      headingFontFamily: 'Playfair Display, serif',
      baseFontSize: '16px',
      headingWeight: '700',
      bodyWeight: '400',
      lineHeight: '1.6',
      headingLineHeight: '1.2',
    },
    {
      fontFamily: 'Nunito, sans-serif',
      headingFontFamily: 'Nunito, sans-serif',
      baseFontSize: '16px',
      headingWeight: '800',
      bodyWeight: '400',
      lineHeight: '1.6',
      headingLineHeight: '1.3',
    },
  ];
};

// Image Utilities
export const getImagePlaceholder = (width: number, height: number, text?: string): string => {
  const placeholderText = text || `${width}x${height}`;
  return `https://via.placeholder.com/${width}x${height}/e5e7eb/6b7280?text=${encodeURIComponent(placeholderText)}`;
};

export const optimizeImageUrl = (url: string, width?: number, height?: number): string => {
  // This would integrate with image optimization service
  // For now, return the original URL
  return url;
};

// SEO Utilities
export const generateMetaTags = (title: string, description: string, image?: string, url?: string) => {
  const metaTags = [
    { name: 'title', content: title },
    { name: 'description', content: description },
    { property: 'og:title', content: title },
    { property: 'og:description', content: description },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: title },
    { name: 'twitter:description', content: description },
  ];

  if (image) {
    metaTags.push(
      { property: 'og:image', content: image },
      { name: 'twitter:image', content: image }
    );
  }

  if (url) {
    metaTags.push({ property: 'og:url', content: url });
  }

  return metaTags;
};

// Local Storage Utilities
export const saveToLocalStorage = (key: string, data: any): void => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
};

export const loadFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Failed to load from localStorage:', error);
    return defaultValue;
  }
};

export const removeFromLocalStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Failed to remove from localStorage:', error);
  }
};

// File Utilities
export const downloadFile = (content: string, filename: string, contentType: string = 'text/plain'): void => {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
};

// Debounce Utility
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Throttle Utility
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Error Handling
export const handleError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
};

// Browser Detection
export const getBrowserInfo = () => {
  const userAgent = navigator.userAgent;
  const isChrome = userAgent.includes('Chrome');
  const isFirefox = userAgent.includes('Firefox');
  const isSafari = userAgent.includes('Safari') && !isChrome;
  const isEdge = userAgent.includes('Edge');
  
  return {
    isChrome,
    isFirefox,
    isSafari,
    isEdge,
    userAgent,
  };
};

// Device Detection
export const getDeviceInfo = () => {
  const userAgent = navigator.userAgent;
  const isMobile = /Mobile|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  const isTablet = /iPad|Android(?=.*Mobile)/i.test(userAgent);
  const isDesktop = !isMobile && !isTablet;
  
  return {
    isMobile,
    isTablet,
    isDesktop,
  };
};

export default {
  generateId,
  slugify,
  truncate,
  capitalize,
  formatDate,
  hexToRgb,
  rgbToHex,
  lightenColor,
  darkenColor,
  isValidEmail,
  isValidUrl,
  isValidHexColor,
  shuffle,
  chunk,
  deepClone,
  omit,
  pick,
  createDefaultWebsite,
  createDefaultPage,
  createDefaultSection,
  getDefaultGlobalStyles,
  getDefaultSectionStyles,
  generateColorPalette,
  getFontPairings,
  getImagePlaceholder,
  optimizeImageUrl,
  generateMetaTags,
  saveToLocalStorage,
  loadFromLocalStorage,
  removeFromLocalStorage,
  downloadFile,
  readFileAsText,
  debounce,
  throttle,
  handleError,
  getBrowserInfo,
  getDeviceInfo,
};