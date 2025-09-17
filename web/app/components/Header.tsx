'use client'

import { RefreshCw, Calendar, Users, Utensils, DollarSign } from 'lucide-react'
import { HeaderProps } from '../../lib/types'
import { formatDistanceToNow } from 'date-fns'

export default function Header({ stats, isLoading, onRefresh, lastUpdated }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-primary">Harvard Events</h1>
          {lastUpdated && (
            <span className="text-sm text-muted-foreground">
              Updated {formatDistanceToNow(lastUpdated, { addSuffix: true })}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          {stats && (
            <div className="hidden md:flex items-center space-x-6 text-sm text-muted-foreground">
              <div className="flex items-center space-x-1">
                <Calendar className="h-4 w-4" />
                <span>{stats.total_events} events</span>
              </div>
              <div className="flex items-center space-x-1">
                <Utensils className="h-4 w-4" />
                <span>{stats.events_with_food} with food</span>
              </div>
              <div className="flex items-center space-x-1">
                <DollarSign className="h-4 w-4" />
                <span>{stats.free_events} free</span>
              </div>
            </div>
          )}
          
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </header>
  )
}
