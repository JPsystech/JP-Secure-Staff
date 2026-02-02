'use client'

import { useState, useEffect } from 'react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiRequest } from '@/lib/api'
import { UserPlus, FileText } from 'lucide-react'
import Link from 'next/link'

interface Person {
  id: string
  name: string
  mobile: string
  email?: string
  status: string
  employee_code?: string
  created_at: string
  stream?: string
}

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchPersons() {
      setLoading(true)
      setError(null)
      try {
        const response = await apiRequest<Person[]>('/persons')
        if (cancelled) return
        if (response.data) {
          setPersons(response.data)
        } else if (response.error) {
          setError(response.error)
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load persons')
        if (process.env.NODE_ENV === 'development') {
          console.debug('[Persons] fetch error', err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchPersons()
    return () => { cancelled = true }
  }, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Persons"
        subtitle="View and manage person profiles"
        actions={
          <Button asChild>
            <Link href="/persons/new" prefetch={false}>
              <UserPlus className="h-4 w-4 mr-2" />
              Create Person
            </Link>
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="p-8 text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>{error}</p>
            </div>
          ) : persons.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No persons yet.</p>
              <Button variant="outline" className="mt-4" asChild>
                <Link href="/persons/new" prefetch={false}>Create Person</Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Mobile</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {persons.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>{p.mobile}</TableCell>
                    <TableCell>{p.email ?? '—'}</TableCell>
                    <TableCell>{p.status}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(p.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
