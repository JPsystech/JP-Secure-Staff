'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { auth, admin, type AdminPersonDocItem } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft, Download } from 'lucide-react'

export default function AdminPersonDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const personId = params.id as string
  const [person, setPerson] = useState<any>(null)
  const [docs, setDocs] = useState<AdminPersonDocItem[]>([])
  const [loading, setLoading] = useState(true)
  const [forbidden, setForbidden] = useState(false)
  const [permissionChecked, setPermissionChecked] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  useEffect(() => {
    (async () => {
      const meRes = await auth.me()
      if (meRes.error || !meRes.data) {
        setPermissionChecked(true)
        return
      }
      const codes = (meRes.data as { permission_codes?: string[] }).permission_codes || []
      if (!codes.includes('ADMIN_PERSON_VIEW_ALL')) {
        setForbidden(true)
      }
      setPermissionChecked(true)
    })()
  }, [])

  useEffect(() => {
    if (!permissionChecked || forbidden || !personId) return
    (async () => {
      setLoading(true)
      const [personRes, docsRes] = await Promise.all([
        admin.getPerson(personId),
        admin.getPersonDocs(personId),
      ])
      if (personRes.error) {
        if (personRes.error.includes('403') || personRes.error.includes('Missing required permission')) {
          setForbidden(true)
        }
      } else if (personRes.data) {
        setPerson(personRes.data)
      }
      if (docsRes.error) {
        setDocs([])
      } else if (docsRes.data?.items) {
        setDocs(docsRes.data.items)
      }
      setLoading(false)
    })()
  }, [permissionChecked, forbidden, personId])

  const handleDownload = async (doc: AdminPersonDocItem) => {
    setDownloadingId(doc.id)
    try {
      await admin.downloadDoc(doc.id, doc.filename || doc.doc_name)
      toast({ title: 'Download started', description: doc.filename || doc.doc_name })
    } catch (e) {
      toast({
        title: 'Download failed',
        description: e instanceof Error ? e.message : 'Forbidden or network error',
        variant: 'destructive',
      })
    } finally {
      setDownloadingId(null)
    }
  }

  if (!permissionChecked) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <div className="p-6 flex justify-center">Loading...</div>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  if (forbidden) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <div className="p-6">
            <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded">
              You don&apos;t have permission to view this person. Required: ADMIN_PERSON_VIEW_ALL.
            </div>
          </div>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <div className="p-6">
          <Button variant="ghost" className="mb-4" onClick={() => router.push('/admin/persons')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Persons
          </Button>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : person ? (
            <>
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Person</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-2">
                  <p><span className="font-medium">Name:</span> {person.name}</p>
                  <p><span className="font-medium">Employee Code:</span> {person.employee_code || '-'}</p>
                  <p><span className="font-medium">Department:</span> {person.department_name || '-'}</p>
                  <p><span className="font-medium">Status:</span> {person.status || '-'}</p>
                  <p><span className="font-medium">Email:</span> {person.email || '-'}</p>
                  <p><span className="font-medium">Mobile:</span> {person.mobile || '-'}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Documents</CardTitle>
                </CardHeader>
                <CardContent>
                  {docs.length === 0 ? (
                    <p className="text-gray-500">No documents.</p>
                  ) : (
                    <ResponsiveTableScroll minWidth={600}>
                      <table className="min-w-full divide-y divide-border">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category / Stage</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {docs.map((doc) => (
                            <tr key={doc.id}>
                              <td className="px-4 py-3 text-sm text-gray-900">{doc.filename || doc.doc_name}</td>
                              <td className="px-4 py-3 text-sm text-gray-500">{doc.doc_category || doc.stage || '-'}</td>
                              <td className="px-4 py-3 text-sm text-gray-500">{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : '-'}</td>
                              <td className="px-4 py-3 text-right">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  disabled={downloadingId === doc.id}
                                  onClick={() => handleDownload(doc)}
                                >
                                  <Download className="w-4 h-4 mr-1" />
                                  {downloadingId === doc.id ? '...' : 'Download'}
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </ResponsiveTableScroll>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-8 text-gray-500">Person not found.</div>
          )}
        </div>
      </AdminShell>
    </ProtectedRoute>
  )
}
