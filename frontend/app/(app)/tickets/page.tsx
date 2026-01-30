'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { Plus, Eye, MoreHorizontal, Ticket } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

interface Ticket {
  id: string
  ticket_no: string
  from_dept_name: string
  to_dept_name: string
  person_name?: string
  category: string
  priority: string
  status: string
  subject: string
  created_at: string
}

export default function TicketsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTickets()
  }, [])

  const fetchTickets = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Ticket[]>('/tickets?scope=my')
      if (response.data) {
        setTickets(response.data)
      } else if (response.error) {
        toast({
          title: 'Error',
          description: response.error,
          variant: 'destructive',
        })
      }
    } catch (err) {
      console.error('Failed to fetch tickets')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Tickets"
        subtitle="Tickets created by you"
        actions={
          <Button onClick={() => router.push('/tickets/new')}>
            <Plus className="w-4 h-4 mr-2" />
            Create Ticket
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : tickets.length === 0 ? (
            <EmptyState
              icon={<Ticket className="h-6 w-6" />}
              title="No tickets found"
              description="Create a ticket to get started."
              action={
                <Button variant="outline" onClick={() => router.push('/tickets/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create your first ticket
                </Button>
              }
              className="m-6"
            />
          ) : (
<ResponsiveTableScroll minWidth={800}>
            <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket No</TableHead>
                    <TableHead>To Dept</TableHead>
                    <TableHead>Person</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[70px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tickets.map((ticket) => (
                    <TableRow key={ticket.id} className="hover:bg-muted/50">
                      <TableCell className="font-medium">{ticket.ticket_no}</TableCell>
                      <TableCell>{ticket.to_dept_name}</TableCell>
                      <TableCell className="text-muted-foreground">{ticket.person_name || '—'}</TableCell>
                      <TableCell>{ticket.category}</TableCell>
                      <TableCell>
                        <StatusBadge status={ticket.priority} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={ticket.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(ticket.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Actions</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => router.push(`/tickets/${ticket.id}`)}>
                              <Eye className="h-4 w-4 mr-2" />
                              Open
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTableScroll>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

