# Harvard Events Web Dashboard

Modern React dashboard for browsing and filtering Harvard mailing list events.

## Features

- **Real-time Updates**: Auto-refreshes every 60 seconds
- **Advanced Filtering**: Filter by list, type, date range, food, and free status
- **Smart Search**: Full-text search across titles, subjects, and locations
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Built with Tailwind CSS and shadcn/ui components
- **TypeScript**: Fully typed for better development experience

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Set environment variables:**
   ```bash
   # Create .env.local
   echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Configuration

### Environment Variables

Create a `.env.local` file in the web directory:

```env
# API base URL (default: http://localhost:8000)
NEXT_PUBLIC_API_BASE=http://localhost:8000

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=true
```

### API Integration

The web app expects the API to be running on `http://localhost:8000` by default. Make sure the FastAPI service is running before starting the web app.

## Features Overview

### Event Cards
- **Title and List**: Event title with source list tag
- **Time and Location**: Formatted date/time and location
- **Event Type**: Color-coded badges for different event types
- **Food/Free Indicators**: Visual indicators for food and free events
- **Confidence Score**: Parsing confidence (0-3 stars)
- **Links**: Direct links to registration pages
- **Expandable Details**: Click to see full description and metadata

### Filtering System
- **Search**: Full-text search across all event fields
- **List Filter**: Multi-select filter by source list tags
- **Event Type**: Filter by event type (info session, workshop, etc.)
- **Date Range**: Filter by start date range
- **Food/Free**: Toggle filters for food and free events
- **Sorting**: Sort by date, title, list, or type

### Real-time Updates
- **Auto-refresh**: Updates every 60 seconds automatically
- **Manual Refresh**: Click refresh button for immediate update
- **Last Updated**: Shows when data was last refreshed
- **Loading States**: Skeleton loaders during data fetching

## Component Architecture

### Pages
- `app/page.tsx` - Main events listing page
- `app/events/page.tsx` - Alternative events page (same functionality)

### Components
- `app/components/Header.tsx` - Top navigation with stats and refresh
- `app/components/Filters.tsx` - Advanced filtering interface
- `app/components/EventCard.tsx` - Individual event display card

### Utilities
- `lib/api.ts` - API client with error handling
- `lib/types.ts` - TypeScript type definitions
- `lib/utils.ts` - Utility functions for formatting and styling

## Styling

The app uses Tailwind CSS with a custom design system:

### Color Scheme
- **Primary**: Blue for main actions and highlights
- **Secondary**: Gray for secondary elements
- **Success**: Green for food/free indicators
- **Warning**: Yellow for medium confidence
- **Danger**: Red for low confidence and errors

### Components
- **Cards**: Rounded corners with subtle shadows
- **Badges**: Color-coded event type indicators
- **Buttons**: Consistent hover states and transitions
- **Forms**: Clean input styling with focus states

## Development

### Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Code Structure

```
web/
├── app/                    # Next.js 14 App Router
│   ├── components/         # React components
│   ├── events/            # Events page
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── lib/                   # Utilities and types
│   ├── api.ts            # API client
│   ├── types.ts          # TypeScript types
│   └── utils.ts          # Utility functions
├── styles/               # CSS files
│   └── globals.css       # Tailwind CSS
└── public/               # Static assets
```

### TypeScript

The app is fully typed with TypeScript:
- API responses are typed
- Component props are typed
- State management is typed
- Error handling is typed

### Error Handling

- **API Errors**: Graceful handling of network and server errors
- **Loading States**: Skeleton loaders and loading indicators
- **Empty States**: Helpful messages when no data is found
- **Retry Logic**: Easy retry for failed requests

## Performance

### Optimization Features
- **Lazy Loading**: Components load as needed
- **Pagination**: Load events in batches of 50
- **Debounced Search**: Search input is debounced
- **Memoization**: Expensive calculations are memoized
- **Image Optimization**: Next.js automatic image optimization

### Bundle Size
- **Tree Shaking**: Unused code is eliminated
- **Code Splitting**: Routes are split into separate chunks
- **Dynamic Imports**: Heavy components are loaded dynamically

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile**: iOS Safari, Chrome Mobile
- **Responsive**: Works on all screen sizes
- **Accessibility**: WCAG 2.1 AA compliant

## Troubleshooting

### Common Issues

1. **API Connection Error**
   - Check if API server is running on port 8000
   - Verify `NEXT_PUBLIC_API_BASE` environment variable
   - Check browser console for CORS errors

2. **No Events Showing**
   - Verify database has events (run ingestion)
   - Check API health endpoint
   - Try clearing filters

3. **Styling Issues**
   - Ensure Tailwind CSS is properly configured
   - Check for CSS conflicts
   - Verify component imports

4. **TypeScript Errors**
   - Run `npm run lint` to check for issues
   - Ensure all types are properly imported
   - Check API response format matches types

### Debug Mode

Enable debug mode by setting `NEXT_PUBLIC_DEBUG=true` in `.env.local`:

```env
NEXT_PUBLIC_DEBUG=true
```

This will enable:
- Additional console logging
- API request/response logging
- Performance timing
- Error stack traces

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Other Platforms

The app can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- Heroku
- Docker

### Environment Variables for Production

```env
NEXT_PUBLIC_API_BASE=https://your-api-domain.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
