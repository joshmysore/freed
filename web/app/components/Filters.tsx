'use client'

import { useState } from 'react'
import { Search, Filter, X, Calendar, MapPin, Tag, Utensils, DollarSign } from 'lucide-react'
import { FiltersProps, FilterState } from '../../lib/types'
import { cn } from '../../lib/utils'

export default function Filters({ 
  filters, 
  onFiltersChange, 
  listTags, 
  eventTypes, 
  isLoading = false 
}: FiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const handleListTagToggle = (tag: string) => {
    const newTags = filters.source_list_tag.includes(tag)
      ? filters.source_list_tag.filter(t => t !== tag)
      : [...filters.source_list_tag, tag]
    onFiltersChange({ source_list_tag: newTags })
  }
  
  const handleEventTypeToggle = (type: string) => {
    const newTypes = filters.etype.includes(type)
      ? filters.etype.filter(t => t !== type)
      : [...filters.etype, type]
    onFiltersChange({ etype: newTypes })
  }
  
  const handleDateRangeChange = (field: 'after' | 'before', value: string) => {
    onFiltersChange({
      date_range: {
        ...filters.date_range,
        [field]: value || undefined
      }
    })
  }
  
  const clearFilters = () => {
    onFiltersChange({
      source_list_tag: [],
      etype: [],
      has_food: null,
      free: null,
      date_range: {},
      search: '',
      sort_by: 'start',
      sort_order: 'desc'
    })
  }
  
  const activeFiltersCount = 
    filters.source_list_tag.length +
    filters.etype.length +
    (filters.has_food !== null ? 1 : 0) +
    (filters.free !== null ? 1 : 0) +
    (filters.date_range.after ? 1 : 0) +
    (filters.date_range.before ? 1 : 0) +
    (filters.search ? 1 : 0)
  
  return (
    <div className="sticky top-16 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Filters</h2>
            {activeFiltersCount > 0 && (
              <span className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
                {activeFiltersCount}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
            {activeFiltersCount > 0 && (
              <button
                onClick={clearFilters}
                className="text-sm text-muted-foreground hover:text-foreground flex items-center space-x-1"
              >
                <X className="h-4 w-4" />
                <span>Clear all</span>
              </button>
            )}
          </div>
        </div>
        
        {/* Search and basic filters */}
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search events..."
              value={filters.search}
              onChange={(e) => onFiltersChange({ search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={filters.has_food === true}
                onChange={(e) => onFiltersChange({ has_food: e.target.checked ? true : null })}
                className="rounded border-input"
                disabled={isLoading}
              />
              <span className="text-sm flex items-center space-x-1">
                <Utensils className="h-4 w-4" />
                <span>Has food</span>
              </span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={filters.free === true}
                onChange={(e) => onFiltersChange({ free: e.target.checked ? true : null })}
                className="rounded border-input"
                disabled={isLoading}
              />
              <span className="text-sm flex items-center space-x-1">
                <DollarSign className="h-4 w-4" />
                <span>Free</span>
              </span>
            </label>
          </div>
        </div>
        
        {/* Expanded filters */}
        {isExpanded && (
          <div className="space-y-4">
            {/* List tags */}
            <div>
              <h3 className="text-sm font-medium mb-2 flex items-center space-x-1">
                <Tag className="h-4 w-4" />
                <span>Lists ({filters.source_list_tag.length})</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {listTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => handleListTagToggle(tag)}
                    className={cn(
                      "px-3 py-1 text-sm rounded-full border transition-colors",
                      filters.source_list_tag.includes(tag)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground border-input hover:bg-accent"
                    )}
                    disabled={isLoading}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Event types */}
            <div>
              <h3 className="text-sm font-medium mb-2">Event Types ({filters.etype.length})</h3>
              <div className="flex flex-wrap gap-2">
                {eventTypes.map(type => (
                  <button
                    key={type}
                    onClick={() => handleEventTypeToggle(type)}
                    className={cn(
                      "px-3 py-1 text-sm rounded-full border transition-colors",
                      filters.etype.includes(type)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground border-input hover:bg-accent"
                    )}
                    disabled={isLoading}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Date range */}
            <div>
              <h3 className="text-sm font-medium mb-2 flex items-center space-x-1">
                <Calendar className="h-4 w-4" />
                <span>Date Range</span>
              </h3>
              <div className="flex items-center space-x-4">
                <div>
                  <label className="text-xs text-muted-foreground">From</label>
                  <input
                    type="date"
                    value={filters.date_range.after || ''}
                    onChange={(e) => handleDateRangeChange('after', e.target.value)}
                    className="px-3 py-2 text-sm border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    disabled={isLoading}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">To</label>
                  <input
                    type="date"
                    value={filters.date_range.before || ''}
                    onChange={(e) => handleDateRangeChange('before', e.target.value)}
                    className="px-3 py-2 text-sm border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    disabled={isLoading}
                  />
                </div>
              </div>
            </div>
            
            {/* Sort options */}
            <div>
              <h3 className="text-sm font-medium mb-2">Sort By</h3>
              <div className="flex items-center space-x-4">
                <select
                  value={filters.sort_by}
                  onChange={(e) => onFiltersChange({ sort_by: e.target.value as any })}
                  className="px-3 py-2 text-sm border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={isLoading}
                >
                  <option value="start">Date</option>
                  <option value="title">Title</option>
                  <option value="source_list_tag">List</option>
                  <option value="etype">Type</option>
                </select>
                
                <select
                  value={filters.sort_order}
                  onChange={(e) => onFiltersChange({ sort_order: e.target.value as any })}
                  className="px-3 py-2 text-sm border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={isLoading}
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
