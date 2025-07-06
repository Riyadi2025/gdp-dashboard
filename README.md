# Pro Factory - Sports Video Analysis Platform

A modern, responsive web application for sports video analysis, inspired by Spiideo's design and functionality. Pro Factory focuses on video upload and URL-based analysis rather than camera recording.

## 🚀 Features

### Core Functionality
- **Video Upload**: Drag-and-drop or click to upload video files (MP4, AVI, MOV, MKV)
- **URL Analysis**: Analyze videos directly from URLs (YouTube, Vimeo, etc.)
- **AI-Powered Analysis**: Simulated sports video analysis with performance metrics
- **Real-time Progress**: Live progress tracking during video processing
- **Results Dashboard**: Interactive modal showing analysis results

### Design & UX
- **Modern Dark Theme**: Professional dark UI similar to Spiideo
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Smooth Animations**: Engaging transitions and hover effects
- **Accessibility**: Keyboard navigation and screen reader support
- **Professional Typography**: Clean, readable fonts with proper hierarchy

### Technical Features
- **Pure Frontend**: No backend required - runs entirely in browser
- **File Validation**: Checks file type and size before processing
- **Error Handling**: User-friendly error messages and validation
- **Mobile Navigation**: Hamburger menu for mobile devices
- **Smooth Scrolling**: Seamless navigation between sections

## 🎯 Sports Supported

- ⚽ Soccer/Football
- 🏀 Basketball
- 🏒 Ice Hockey
- ⚾ Baseball
- 🏈 American Football
- 🎾 Tennis
- 🏐 Volleyball
- 🏉 Rugby
- And many more...

## 🛠️ How to Use

### 1. Upload Video
- Go to the "Upload & Analyze" section
- Either drag and drop a video file or click "browse files"
- Supported formats: MP4, AVI, MOV, MKV (up to 2GB)
- Wait for processing to complete

### 2. Analyze from URL
- Enter a video URL in the URL input field
- Click "Analyze" button
- System will process the video from the provided URL

### 3. View Results
- After processing, a results modal will appear
- Shows performance metrics, key plays, and analysis insights
- Click "View Full Report" to see detailed analysis (demo)

## 🔧 Technical Implementation

### File Structure
```
pro-factory/
├── index.html          # Main HTML file
├── style.css           # Comprehensive CSS styling
├── script.js           # JavaScript functionality
└── README.md          # This documentation
```

### Key Components

#### HTML Structure
- Semantic HTML5 elements
- Accessible navigation with ARIA labels
- Responsive grid layouts
- Form elements with proper validation

#### CSS Features
- CSS Grid and Flexbox for layouts
- Custom animations and transitions
- Responsive breakpoints
- CSS variables for consistent theming
- Modern hover effects and interactions

#### JavaScript Functionality
- File upload with drag-and-drop
- URL validation and processing
- Progress tracking simulation
- Modal dialogs for results
- Mobile navigation toggle
- Smooth scrolling navigation
- Keyboard shortcuts (ESC to close, Ctrl+U for upload)

## 📱 Responsive Design

### Desktop (1200px+)
- Full navigation menu
- Two-column layouts
- Large hero section
- Grid-based feature cards

### Tablet (768px - 1199px)
- Adjusted grid layouts
- Optimized spacing
- Touch-friendly buttons

### Mobile (< 768px)
- Hamburger navigation
- Single-column layouts
- Stacked upload methods
- Touch-optimized interactions

## 🎨 Design System

### Colors
- **Primary**: #00d4ff (Cyan Blue)
- **Secondary**: #0099cc (Dark Blue)
- **Background**: #0a0a0a (Near Black)
- **Surface**: #1a1a1a (Dark Gray)
- **Text**: #ffffff (White)
- **Muted**: #cccccc (Light Gray)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700
- **Responsive sizing**: rem units for scalability

### Spacing
- **Container**: 1200px max-width
- **Sections**: 100px vertical padding
- **Cards**: 30px padding
- **Gaps**: 20px, 30px, 40px, 60px

## 🚀 Getting Started

1. **Download the files**
   - Save `index.html`, `style.css`, and `script.js` in the same folder

2. **Open in browser**
   - Double-click `index.html` to open in your default browser
   - Or use a local server for best performance

3. **Test the features**
   - Try uploading a video file
   - Test URL analysis with a video URL
   - Explore the responsive design on different devices

## 🔄 Customization

### Branding
- Update the logo/brand name in the HTML
- Modify colors in the CSS variables
- Change the hero text and messaging

### Functionality
- Replace simulation functions with real API calls
- Add backend integration for actual video processing
- Implement user authentication and accounts
- Add data persistence and user profiles

### Sports
- Add more sport-specific analysis features
- Customize metrics for different sports
- Add sport-specific UI elements

## 📊 Simulated Analysis Results

The demo shows sample analysis results including:
- **Performance Score**: Overall game performance percentage
- **Key Plays**: Number of significant moments identified
- **Players Tracked**: Number of players analyzed
- **Success Rate**: Percentage of successful plays/actions

## 🛡️ Security Considerations

- File type validation prevents malicious uploads
- URL validation ensures only valid URLs are processed
- No server-side processing in this demo version
- Client-side only - no data persistence

## 🌟 Future Enhancements

- Real AI video analysis integration
- User account management
- Team collaboration features
- Advanced analytics dashboard
- Video annotation tools
- Export functionality for reports
- Integration with sports databases

## 📞 Support

For questions or issues:
- Check the browser console for error messages
- Ensure your browser supports modern JavaScript features
- Test with different video formats and sizes
- Try the URL analysis with publicly accessible video URLs

---

**Pro Factory** - Transform your game analysis with intelligent video insights! 🚀
