'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageShell, DataCard, EmptyState, TableSkeleton } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/components/ui/use-toast'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { apiRequest } from '@/lib/api'
import { Plus, Edit, Shield } from 'lucide-react'

interface Policy {
  id: number
  key: string
  value_json: unknown
  updated_by: number
  updated_at: string
}

export default function PoliciesPage() {
  const { toast } = useToast()
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null)
  const [formData, setFormData] = useState({ key: '', value_json: '{}' })
  const [formError, setFormError] = useState('')

  const fetchPolicies = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Policy[]>('/policies')
      if (response.data) {
        setPolicies(response.data)
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to fetch policies', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPolicies()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    try {
      let valueJson: unknown
      try {
        valueJson = JSON.parse(formData.value_json)
      } catch {
        setFormError('Invalid JSON format')
        return
      }

      if (editingPolicy) {
        const response = await apiRequest<Policy>(`/policies/${editingPolicy.key}`, {
          method: 'PATCH',
          body: JSON.stringify({ value_json: valueJson }),
        })
        if (response.error) {
          setFormError(response.error)
          return
        }
        toast({ title: 'Policy updated' })
      } else {
        const response = await apiRequest<Policy>('/policies', {
          method: 'POST',
          body: JSON.stringify({ key: formData.key, value_json: valueJson }),
        })
        if (response.error) {
          setFormError(response.error)
          return
        }
        toast({ title: 'Policy created' })
      }
      setShowModal(false)
      setEditingPolicy(null)
      setFormData({ key: '', value_json: '{}' })
      fetchPolicies()
    } catch {
      setFormError('An error occurred')
    }
  }

  const handleEdit = (policy: Policy) => {
    setEditingPolicy(policy)
    setFormData({
      key: policy.key,
      value_json: JSON.stringify(policy.value_json, null, 2),
    })
    setShowModal(true)
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
            title="Policies"
            subtitle="Manage system policy key-value settings"
            actions={
              <Button
                onClick={() => {
                  setEditingPolicy(null)
                  setFormData({ key: '', value_json: '{}' })
                  setShowModal(true)
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Policy
              </Button>
            }
          >
            {loading ? (
              <TableSkeleton rows={6} cols={4} />
            ) : policies.length === 0 ? (
              <EmptyState
                icon={<Shield className="h-6 w-6" />}
                title="No policies"
                description="Add a policy to configure system behaviour."
                action={
                  <Button onClick={() => { setEditingPolicy(null); setFormData({ key: '', value_json: '{}' }); setShowModal(true); }}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Policy
                  </Button>
                }
              />
            ) : (
              <DataCard
                title="Policies"
                description={`${policies.length} policy entries`}
                icon={<Shield className="h-4 w-4" />}
                noPadding
              >
                <ResponsiveTableScroll minWidth={700}>
                  <Table className="min-w-[700px]">
                    <TableHeader>
                      <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                        <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Key</TableHead>
                        <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Value</TableHead>
                        <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Updated</TableHead>
                        <TableHead className="text-xs uppercase tracking-wide text-muted-foreground text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {policies.map((policy) => (
                        <TableRow key={policy.id} className="hover:bg-muted/50">
                          <TableCell className="font-medium">{policy.key}</TableCell>
                          <TableCell className="text-sm text-muted-foreground max-w-[280px]">
                            <pre className="text-xs overflow-auto whitespace-pre-wrap">{JSON.stringify(policy.value_json, null, 2)}</pre>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                            {new Date(policy.updated_at).toLocaleString()}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button variant="outline" size="sm" onClick={() => handleEdit(policy)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ResponsiveTableScroll>
              </DataCard>
            )}
          </PageShell>

          <Dialog
            open={showModal}
            onOpenChange={(open) => {
              if (!open) {
                setShowModal(false)
                setEditingPolicy(null)
                setFormData({ key: '', value_json: '' })
                setFormError('')
              }
            }}
          >
            <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingPolicy ? 'Edit Policy' : 'Add Policy'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key">Key</Label>
                  <Input
                    id="key"
                    value={formData.key}
                    onChange={(e) => setFormData({ ...formData, key: e.target.value })}
                    required
                    disabled={!!editingPolicy}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="value_json">Value (JSON)</Label>
                  <textarea
                    id="value_json"
                    value={formData.value_json}
                    onChange={(e) => setFormData({ ...formData, value_json: e.target.value })}
                    required
                    rows={10}
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                  />
                </div>
                {formError && <p className="text-sm text-destructive">{formError}</p>}
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => { setShowModal(false); setEditingPolicy(null); setFormData({ key: '', value_json: '' }); setFormError(''); }}>Cancel</Button>
                  <Button type="submit">{editingPolicy ? 'Update' : 'Create'}</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
      </AdminShell>
    </ProtectedRoute>
  )
}
