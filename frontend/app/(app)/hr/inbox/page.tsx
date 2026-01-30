'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { Eye, FileText } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email: string
  status: string
  employee_code?: string
  company_name?: string
}

export default function HRInboxPage() {
  const router = useRouter()
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInbox()
  }, [])

  const fetchInbox = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Person[]>('/hr/inbox')
      if (response.data) {
        setPersons(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch inbox')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="HR Inbox"
        subtitle="Persons sent to HR for processing"
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : persons.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No persons in HR inbox</h3>
              <p className="text-sm text-gray-500">
                Persons will appear here after Finance submits them
              </p>
            </div>
          ) : (
            <ResponsiveTableScroll minWidth={700}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Mobile</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Employee Code</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {persons.map((person) => (
                    <TableRow key={person.id}>
                      <TableCell className="font-medium">{person.name}</TableCell>
                      <TableCell>{person.mobile}</TableCell>
                      <TableCell>{person.email || '—'}</TableCell>
                      <TableCell>
                        {person.employee_code ? (
                          <Badge variant="secondary">{person.employee_code}</Badge>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{person.status}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/persons/${person.id}?tab=hr`)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          Open
                        </Button>
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

