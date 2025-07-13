import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import { 
  EyeIcon, 
  DevicePhoneMobileIcon, 
  ComputerDesktopIcon,
  PaintBrushIcon,
  Cog6ToothIcon,
  DocumentArrowDownIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

export default function Editor() {
  const router = useRouter();
  const [websiteData, setWebsiteData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'edit' | 'design' | 'settings'>('edit');
  const [viewMode, setViewMode] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [isPreview, setIsPreview] = useState(false);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('generatedWebsite');
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setWebsiteData(data);
      } catch (error) {
        console.error('Error parsing stored website data:', error);
        toast.error('Error loading website data');
        router.push('/');
      }
    } else {
      router.push('/');
    }
  }, [router]);

  const handleSectionClick = (sectionId: string) => {
    if (!isPreview) {
      setSelectedSection(sectionId);
    }
  };

  const handlePublish = async () => {
    if (!websiteData) return;

    try {
      const response = await fetch('/api/websites/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(websiteData),
      });

      const result = await response.json();

      if (result.success) {
        toast.success('Website published successfully!');
        window.open(result.url, '_blank');
      } else {
        toast.error(result.error || 'Failed to publish website');
      }
    } catch (error) {
      console.error('Publish error:', error);
      toast.error('An error occurred while publishing your website');
    }
  };

  const handleExport = () => {
    if (!websiteData) return;

    const htmlContent = generateHTMLFromData(websiteData);
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${websiteData.name || 'website'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Website exported successfully!');
  };

  const generateHTMLFromData = (data: any): string => {
    if (!data || !data.pages || !data.pages[0]) return '';

    const page = data.pages[0];
    const sections = page.sections || [];
    const theme = data.theme || {};

    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${data.name || 'Website'}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: ${theme.typography?.fontFamily || 'Inter, sans-serif'};
      line-height: 1.6;
      color: ${theme.colors?.text || '#1f2937'};
      background-color: ${theme.colors?.background || '#ffffff'};
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 20px;
    }
    
    .section {
      padding: 60px 0;
    }
    
    .hero {
      background: linear-gradient(135deg, ${theme.colors?.primary || '#3b82f6'}, ${theme.colors?.secondary || '#64748b'});
      color: white;
      text-align: center;
    }
    
    .hero h1 {
      font-size: 3rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }
    
    .hero p {
      font-size: 1.25rem;
      margin-bottom: 2rem;
    }
    
    .btn {
      display: inline-block;
      padding: 12px 24px;
      background-color: ${theme.colors?.accent || '#06b6d4'};
      color: white;
      text-decoration: none;
      border-radius: 6px;
      font-weight: 600;
      transition: all 0.3s ease;
    }
    
    .btn:hover {
      background-color: ${theme.colors?.primary || '#3b82f6'};
      transform: translateY(-2px);
    }
    
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 2rem;
      margin-top: 2rem;
    }
    
    .card {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .card h3 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      color: ${theme.colors?.primary || '#3b82f6'};
    }
    
    .text-center {
      text-align: center;
    }
    
    .mb-4 {
      margin-bottom: 1rem;
    }
    
    .mb-8 {
      margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
      .hero h1 {
        font-size: 2rem;
      }
      
      .hero p {
        font-size: 1rem;
      }
      
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  ${sections.map((section: any) => generateSectionHTML(section)).join('')}
</body>
</html>
    `;
  };

  const generateSectionHTML = (section: any): string => {
    const { type, content } = section;

    switch (type) {
      case 'hero':
        return `
          <section class="section hero">
            <div class="container">
              <h1>${content.heading || 'Welcome to Our Website'}</h1>
              <p>${content.subheading || 'We create amazing experiences'}</p>
              ${content.buttons?.map((button: any) => `
                <a href="${button.url || '#'}" class="btn">${button.text || 'Learn More'}</a>
              `).join('') || ''}
            </div>
          </section>
        `;
      
      case 'about':
        return `
          <section class="section">
            <div class="container text-center">
              <h2 class="mb-4">${content.heading || 'About Us'}</h2>
              <p class="mb-8">${content.description || 'Learn more about our company and mission.'}</p>
            </div>
          </section>
        `;
      
      case 'services':
        return `
          <section class="section">
            <div class="container">
              <h2 class="text-center mb-8">${content.heading || 'Our Services'}</h2>
              <div class="grid">
                ${content.items?.map((item: any) => `
                  <div class="card">
                    <h3>${item.title || 'Service'}</h3>
                    <p>${item.description || 'Service description'}</p>
                  </div>
                `).join('') || ''}
              </div>
            </div>
          </section>
        `;
      
      case 'contact':
        return `
          <section class="section">
            <div class="container text-center">
              <h2 class="mb-4">${content.heading || 'Contact Us'}</h2>
              <p class="mb-8">${content.description || 'Get in touch with us today.'}</p>
              ${content.buttons?.map((button: any) => `
                <a href="${button.url || '#'}" class="btn">${button.text || 'Contact Us'}</a>
              `).join('') || ''}
            </div>
          </section>
        `;
      
      default:
        return `
          <section class="section">
            <div class="container">
              <h2 class="text-center mb-4">${content.heading || 'Section'}</h2>
              <p class="text-center">${content.description || 'Section content'}</p>
            </div>
          </section>
        `;
    }
  };

  const renderSection = (section: any, index: number) => {
    const { type, content } = section;
    const isSelected = selectedSection === `section-${index}`;
    const sectionClass = `section-preview ${isSelected ? 'selected' : ''}`;

    switch (type) {
      case 'hero':
        return (
          <div 
            key={index} 
            className={sectionClass}
            onClick={() => handleSectionClick(`section-${index}`)}
          >
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20 px-8 text-center">
              <h1 className="text-4xl md:text-6xl font-bold mb-4">
                {content.heading || 'Welcome to Our Website'}
              </h1>
              <p className="text-xl mb-8">
                {content.subheading || 'We create amazing experiences'}
              </p>
              {content.buttons?.map((button: any, btnIndex: number) => (
                <a
                  key={btnIndex}
                  href={button.url || '#'}
                  className="inline-block bg-white text-blue-600 font-semibold py-3 px-6 rounded-lg hover:bg-gray-100 transition-colors mr-4"
                >
                  {button.text || 'Learn More'}
                </a>
              ))}
            </div>
          </div>
        );
      
      case 'about':
        return (
          <div 
            key={index} 
            className={sectionClass}
            onClick={() => handleSectionClick(`section-${index}`)}
          >
            <div className="py-20 px-8 text-center">
              <h2 className="text-3xl font-bold mb-4">
                {content.heading || 'About Us'}
              </h2>
              <p className="text-lg text-gray-600 max-w-3xl mx-auto">
                {content.description || 'Learn more about our company and mission.'}
              </p>
            </div>
          </div>
        );
      
      case 'services':
        return (
          <div 
            key={index} 
            className={sectionClass}
            onClick={() => handleSectionClick(`section-${index}`)}
          >
            <div className="py-20 px-8">
              <h2 className="text-3xl font-bold text-center mb-12">
                {content.heading || 'Our Services'}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {content.items?.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} className="bg-white p-6 rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold mb-2">{item.title || 'Service'}</h3>
                    <p className="text-gray-600">{item.description || 'Service description'}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      
      case 'contact':
        return (
          <div 
            key={index} 
            className={sectionClass}
            onClick={() => handleSectionClick(`section-${index}`)}
          >
            <div className="py-20 px-8 text-center bg-gray-50">
              <h2 className="text-3xl font-bold mb-4">
                {content.heading || 'Contact Us'}
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                {content.description || 'Get in touch with us today.'}
              </p>
              {content.buttons?.map((button: any, btnIndex: number) => (
                <a
                  key={btnIndex}
                  href={button.url || '#'}
                  className="inline-block bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors mr-4"
                >
                  {button.text || 'Contact Us'}
                </a>
              ))}
            </div>
          </div>
        );
      
      default:
        return (
          <div 
            key={index} 
            className={sectionClass}
            onClick={() => handleSectionClick(`section-${index}`)}
          >
            <div className="py-20 px-8 text-center">
              <h2 className="text-3xl font-bold mb-4">
                {content.heading || 'Section'}
              </h2>
              <p className="text-lg text-gray-600">
                {content.description || 'Section content'}
              </p>
            </div>
          </div>
        );
    }
  };

  if (!websiteData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentPage = websiteData.pages?.[0];
  const sections = currentPage?.sections || [];

  return (
    <>
      <Head>
        <title>Website Editor - AI Website Builder</title>
        <meta name="description" content="Edit and customize your AI-generated website" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => router.push('/')}
                  className="text-gray-600 hover:text-blue-600 transition-colors"
                >
                  ← Back to Home
                </button>
                <h1 className="text-xl font-semibold text-gray-900">
                  {websiteData.name || 'Website Editor'}
                </h1>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* View Mode Toggle */}
                <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('desktop')}
                    className={`p-2 rounded ${viewMode === 'desktop' ? 'bg-white shadow-sm' : ''}`}
                  >
                    <ComputerDesktopIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setViewMode('mobile')}
                    className={`p-2 rounded ${viewMode === 'mobile' ? 'bg-white shadow-sm' : ''}`}
                  >
                    <DevicePhoneMobileIcon className="h-5 w-5" />
                  </button>
                </div>

                {/* Preview Toggle */}
                <button
                  onClick={() => setIsPreview(!isPreview)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isPreview 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <EyeIcon className="h-5 w-5" />
                  <span>{isPreview ? 'Exit Preview' : 'Preview'}</span>
                </button>

                {/* Export Button */}
                <button
                  onClick={handleExport}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <DocumentArrowDownIcon className="h-5 w-5" />
                  <span>Export</span>
                </button>

                {/* Publish Button */}
                <button
                  onClick={handlePublish}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <GlobeAltIcon className="h-5 w-5" />
                  <span>Publish</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="flex h-[calc(100vh-80px)]">
          {/* Sidebar */}
          {!isPreview && (
            <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  <button
                    onClick={() => setActiveTab('edit')}
                    className={`py-4 px-2 text-sm font-medium border-b-2 ${
                      activeTab === 'edit'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setActiveTab('design')}
                    className={`py-4 px-2 text-sm font-medium border-b-2 ${
                      activeTab === 'design'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Design
                  </button>
                  <button
                    onClick={() => setActiveTab('settings')}
                    className={`py-4 px-2 text-sm font-medium border-b-2 ${
                      activeTab === 'settings'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Settings
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeTab === 'edit' && (
                  <div>
                    <h3 className="text-lg font-medium mb-4">Sections</h3>
                    <div className="space-y-2">
                      {sections.map((section: any, index: number) => (
                        <div
                          key={index}
                          onClick={() => handleSectionClick(`section-${index}`)}
                          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                            selectedSection === `section-${index}`
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="font-medium capitalize">{section.type}</div>
                          <div className="text-sm text-gray-600 truncate">
                            {section.content?.heading || 'Section content'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'design' && (
                  <div>
                    <h3 className="text-lg font-medium mb-4">Design</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Primary Color
                        </label>
                        <input
                          type="color"
                          value={websiteData.theme?.colors?.primary || '#3b82f6'}
                          className="w-full h-10 rounded border border-gray-300"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Font Family
                        </label>
                        <select className="w-full p-2 border border-gray-300 rounded">
                          <option>Inter</option>
                          <option>Roboto</option>
                          <option>Open Sans</option>
                          <option>Playfair Display</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'settings' && (
                  <div>
                    <h3 className="text-lg font-medium mb-4">Settings</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Website Name
                        </label>
                        <input
                          type="text"
                          value={websiteData.name || ''}
                          className="w-full p-2 border border-gray-300 rounded"
                          placeholder="Enter website name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Description
                        </label>
                        <textarea
                          value={websiteData.description || ''}
                          className="w-full p-2 border border-gray-300 rounded"
                          rows={3}
                          placeholder="Enter website description"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Main Content - Preview */}
          <div className="flex-1 overflow-auto bg-gray-50">
            <div className={`mx-auto transition-all duration-300 ${
              viewMode === 'desktop' ? 'max-w-none' : 
              viewMode === 'tablet' ? 'max-w-3xl' : 'max-w-sm'
            }`}>
              <div className="bg-white min-h-full">
                <style jsx>{`
                  .section-preview {
                    position: relative;
                    cursor: ${isPreview ? 'default' : 'pointer'};
                  }
                  
                  .section-preview:hover {
                    outline: ${isPreview ? 'none' : '2px solid #3b82f6'};
                    outline-offset: -2px;
                  }
                  
                  .section-preview.selected {
                    outline: 2px solid #3b82f6;
                    outline-offset: -2px;
                  }
                `}</style>
                
                {sections.map((section: any, index: number) => 
                  renderSection(section, index)
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}