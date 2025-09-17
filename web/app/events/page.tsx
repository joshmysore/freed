'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Header from '../components/Header'
import Filters from '../components/Filters'
import EventCard from '../components/EventCard'
import { Event, FilterState, StatsResponse } from '../../lib/types'
import { getEvents, getListTags, getEventTypes, getStats } from '../../lib/api'
import { ApiError } from '../../lib/api'

export default function EventsPage() {
  const searchParams = useSearchParams()
  const [events, setEvents] = useState<Event[]>([])
  const [listTags, setListTags] = useState<string[]>([])
  const [eventTypes, setEventTypes] = useState<string[]>([])
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  const [filters, setFilters] = useState<FilterState>({
    source_list_tag: [],
    etype: [],
    has_food: null,
    free: null,
    date_range: {},
    search: '',
    sort_by: 'start',
    sort_order: 'desc'
  })
  
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const limit = 50
  
  // Load initial data
  useEffect(() => {
    loadInitialData()
  }, [])
  
  // Load events when filters change
  useEffect(() => {
    loadEvents()
  }, [filters, offset])
  
  // Auto-refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadEvents(true) // Silent refresh
    }, 60000)
    
    return () => clearInterval(interval)
  }, [filters, offset])
  
  const loadInitialData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const [listTagsData, eventTypesData, statsData] = await Promise.all([
        getListTags(),
        getEventTypes(),
        getStats()
      ])
      
      setListTags(listTagsData.list_tags)
      setEventTypes(eventTypesData.event_types)
      setStats(statsData)
    } catch (err) {
      console.error('Error loading initial data:', err)
      setError(err instanceof ApiError ? err.message : 'Failed to load data')
    }
  }
  
  const loadEvents = async (silent = false) => {
    try {
      if (!silent) {
        setIsLoading(true)
        setError(null)
      }
      
      const query = {
        ...filters,
        limit,
        offset,
        order_by: `${filters.sort_by} ${filters.sort_order}`
      }
      
      // Convert array filters to single values for API
      if (query.source_list_tag.length === 1) {
        query.source_list_tag = query.source_list_tag[0] as any
      } else if (query.source_list_tag.length > 1) {
        // For multiple list tags, we'll need to make multiple requests
        // For now, just use the first one
        query.source_list_tag = query.source_list_tag[0] as any
      } else {
        delete query.source_list_tag
      }
      
      if (query.etype.length === 1) {
        query.etype = query.etype[0] as any
      } else if (query.etype.length > 1) {
        query.etype = query.etype[0] as any
      } else {
        delete query.etype
      }
      
      const response = await getEvents(query)
      setEvents(response.events)
      setTotal(response.total)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Error loading events:', err)
      setError(err instanceof ApiError ? err.message : 'Failed to load events')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleFiltersChange = (newFilters: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
    setOffset(0) // Reset to first page when filters change
  }
  
  const handleRefresh = () => {
    loadEvents()
  }
  
  const handleEventClick = (event: Event) => {
    // Navigate to event detail page or show modal
    console.log('Event clicked:', event)
  }
  
  const handleLoadMore = () => {
    setOffset(prev => prev + limit)
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-destructive mb-4">Error</h1>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen">
      <Header 
        stats={stats} 
        isLoading={isLoading} 
        onRefresh={handleRefresh}
        lastUpdated={lastUpdated}
      />
      
      <Filters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        listTags={listTags}
        eventTypes={eventTypes}
        isLoading={isLoading}
      />
      
      <main className="container py-8">
        {isLoading && events.length === 0 ? (
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="event-card p-6">
                <div className="space-y-4">
                  <div className="skeleton h-6 w-3/4"></div>
                  <div className="skeleton h-4 w-1/2"></div>
                  <div className="skeleton h-4 w-1/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold text-muted-foreground mb-2">
              No events found
            </h2>
            <p className="text-muted-foreground">
              Try adjusting your filters or check back later.
            </p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <p className="text-sm text-muted-foreground">
                Showing {events.length} of {total} events
                {filters.search && ` matching "${filters.search}"`}
              </p>
            </div>
            
            <div className="space-y-4">
              {events.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onEventClick={handleEventClick}
                />
              ))}
            </div>
            
            {events.length < total && (
              <div className="text-center mt-8">
                <button
                  onClick={handleLoadMore}
                  disabled={isLoading}
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
