'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { DocumentsDrawer } from '@/components/cv-wallet/DocumentsDrawer'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { apiRequest } from '@/lib/api'
import { Eye, FileText, MoreHorizontal, UserPlus } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

interface Person {
  id: string
  name: string
  mobile: string
  email: string
  status: string
  employee_code?: string
  created_at: string
  stream?: string
  location?: string
}

export default function MySubmissionsPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [persons, setPersons] = useState<Person[]>([])
  const [filteredPersons, setFilteredPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [myOnly, setMyOnly] = useState(true)
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const userData = JSON.parse(userStr)
      setUser(userData)
    }
  }, [])

  useEffect(() => {
    filterPersons()
  }, [persons, myOnly, user])

  const fetchSubmissions = async () => {
    setLoading(true)
    try {
      // Get persons filtered by current user if "My Only" is enabled
      const userId = myOnly && user && 'id' in user ? (user as any).id : undefined
      const url = userId 
        ? `/persons?created_by=${userId}&limit=1000`
        : '/persons?limit=1000'
      
      const response = await apiRequest<Person[]>(url)
      if (response.data) {
        setPersons(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch submissions')
    } finally {
      setLoading(false)
    }
  }

  const filterPersons = () => {
    let filtered = [...persons]
    
    // Sort by created_at descending
    filtered.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    
    setFilteredPersons(filtered)
  }

  useEffect(() => {
    fetchSubmissions()
  }, [myOnly, user])

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Submissions"
        subtitle="Track all profiles you've created"
        actions={
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                id="my-only"
                checked={myOnly}
                onCheckedChange={setMyOnly}
              />
              <Label htmlFor="my-only" className="cursor-pointer">
                My Only
              </Label>
            </div>
          </div>
        }
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredPersons.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-6 w-6" />}
              title="No submissions found"
              description={myOnly ? "You haven't created any profiles yet" : "No profiles found"}
              action={
                <Button onClick={() => router.push('/operation/create')}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Create Your First Profile
                </Button>
              }
              className="m-4"
            />
          ) : (
<ResponsiveTableScroll minWidth={700}>
            <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Mobile</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Created Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Employee Code</TableHead>
                    <TableHead className="w-[70px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPersons.map((person) => (
                    <TableRow key={person.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <div className="font-medium">{person.name}</div>
                          {person.stream && (
                            <div className="text-xs text-muted-foreground">{person.stream}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{person.mobile}</TableCell>
                      <TableCell>{person.email || '—'}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(person.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={person.status} />
                      </TableCell>
                      <TableCell>
                        {person.employee_code ? (
                          <Badge variant="secondary">{person.employee_code}</Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
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
                            <DropdownMenuItem
                              onClick={() => router.push(`/cv-wallet?person=${person.id}`)}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              Open in CV Wallet
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedPerson(person)
                                setDrawerOpen(true)
                              }}
                            >
                              <FileText className="h-4 w-4 mr-2" />
                              View Documents
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

      {/* Documents Drawer */}
      <DocumentsDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        person={selectedPerson}
      />
    </div>
  )
}

