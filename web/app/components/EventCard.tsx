'use client'

import { useState } from 'react'
import { Calendar, MapPin, Clock, ExternalLink, Users, Utensils, DollarSign, AlertCircle } from 'lucide-react'
import { EventCardProps } from '../../lib/types'
import { formatDate, formatTime, formatDateTime, getEventTypeColor, getConfidenceColor, getConfidenceText, cn } from '../../lib/utils'

export default function EventCard({ event, onEventClick }: EventCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const handleClick = () => {
    if (onEventClick) {
      onEventClick(event)
    } else {
      setIsExpanded(!isExpanded)
    }
  }
  
  const hasTime = event.start && event.start !== 'TBD'
  const hasLocation = event.location && event.location !== 'TBD'
  const hasLinks = event.links && event.links.length > 0
  
  return (
    <div 
      className="event-card p-6 cursor-pointer hover:shadow-lg transition-all duration-200"
      onClick={handleClick}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-foreground line-clamp-2 mb-2">
              {event.title}
            </h3>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span className="font-medium">{event.source_list_tag}</span>
              {event.etype && (
                <>
                  <span>•</span>
                  <span className={cn("badge", getEventTypeColor(event.etype))}>
                    {event.etype}
                  </span>
                </>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            {event.food && (
              <div className="flex items-center space-x-1 text-green-600" title="Has food">
                <Utensils className="h-4 w-4" />
              </div>
            )}
            {event.free && (
              <div className="flex items-center space-x-1 text-green-600" title="Free event">
                <DollarSign className="h-4 w-4" />
              </div>
            )}
            <div 
              className={cn("text-xs", getConfidenceColor(event.confidence))}
              title={`Confidence: ${getConfidenceText(event.confidence)}`}
            >
              {event.confidence}/3
            </div>
          </div>
        </div>
        
        {/* Time and Location */}
        <div className="space-y-2">
          {hasTime && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4 flex-shrink-0" />
              <span>{formatDate(event.start)}</span>
              <Clock className="h-4 w-4 flex-shrink-0" />
              <span>{formatTime(event.start)}</span>
            </div>
          )}
          
          {hasLocation && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <MapPin className="h-4 w-4 flex-shrink-0" />
              <span>{event.location}</span>
            </div>
          )}
        </div>
        
        {/* Links */}
        {hasLinks && (
          <div className="flex items-center space-x-2">
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
            <div className="flex flex-wrap gap-2">
              {event.links.slice(0, 2).map((link, index) => (
                <a
                  key={index}
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {link.includes('eventbrite') ? 'Eventbrite' : 
                   link.includes('google.com/forms') ? 'Google Form' : 
                   'Link'}
                </a>
              ))}
              {event.links.length > 2 && (
                <span className="text-sm text-muted-foreground">
                  +{event.links.length - 2} more
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* Expanded content */}
        {isExpanded && (
          <div className="space-y-4 pt-4 border-t">
            {event.raw_excerpt && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">Event Description</h4>
                <p className="text-sm text-muted-foreground leading-relaxed bg-muted p-3 rounded-md">
                  {event.raw_excerpt}
                </p>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-foreground">Subject:</span>
                <p className="text-muted-foreground mt-1 break-words">{event.subject}</p>
              </div>
              <div>
                <span className="font-medium text-foreground">Received:</span>
                <p className="text-muted-foreground mt-1">
                  {formatDateTime(event.received_utc)}
                </p>
              </div>
              <div>
                <span className="font-medium text-foreground">From List:</span>
                <p className="text-muted-foreground mt-1">{event.source_list_tag}</p>
              </div>
              <div>
                <span className="font-medium text-foreground">Event ID:</span>
                <p className="text-muted-foreground mt-1 font-mono text-xs">{event.id}</p>
              </div>
            </div>
            
            {event.end && event.start && (
              <div className="text-sm">
                <span className="font-medium text-foreground">Duration:</span>
                <span className="text-muted-foreground ml-2">
                  {Math.round((new Date(event.end).getTime() - new Date(event.start).getTime()) / (1000 * 60))} minutes
                </span>
              </div>
            )}
            
            {/* Links section */}
            {hasLinks && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">Links & Registration</h4>
                <div className="space-y-2">
                  {event.links.map((link, index) => (
                    <a
                      key={index}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-sm text-primary hover:underline break-all"
                    >
                      {link.includes('eventbrite') ? '🎫 Eventbrite Registration' :
                       link.includes('forms.gle') || link.includes('google.com/forms') ? '📝 Google Form' :
                       link.includes('signup') ? '📋 Sign Up Form' :
                       link.includes('register') ? '📝 Registration' :
                       '🔗 Link'} - {link}
                    </a>
                  ))}
                </div>
              </div>
            )}
            
            {/* Metadata */}
            <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
              <div className="grid grid-cols-2 gap-2">
                <div>Confidence: {event.confidence}/3</div>
                <div>Food: {event.food ? 'Yes' : 'No'}</div>
                <div>Free: {event.free ? 'Yes' : 'No'}</div>
                <div>Type: {event.etype || 'Unknown'}</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center space-x-4">
            <span>ID: {event.id.slice(0, 8)}...</span>
            {event.confidence < 2 && (
              <div className="flex items-center space-x-1 text-orange-600">
                <AlertCircle className="h-3 w-3" />
                <span>Low confidence</span>
              </div>
            )}
          </div>
          <span>Click to {isExpanded ? 'collapse' : 'expand'}</span>
        </div>
      </div>
    </div>
  )
}
