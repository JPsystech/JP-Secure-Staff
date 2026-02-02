'use client'

import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import UserShell from '@/components/layouts/UserShell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api'
import { Save, Check } from 'lucide-react'
import HRDocumentsPanel from '@/components/hr/HRDocumentsPanel'

interface Person {
  id: string
  name: string
  mobile: string
  email: string
  status: string
  employee_code?: string
  company_name?: string
}

export default function PersonDetailPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const personId = params.id as string
  const activeTab = searchParams.get('tab') || 'overview'
  
  const [person, setPerson] = useState<Person | null>(null)
  const [loading, setLoading] = useState(true)
  const [employmentData, setEmploymentData] = useState({employment_type: '', company_id: ''})
  const [kycData, setKycData] = useState({aadhaar: '', pan: '', bank_account_no: '', ifsc: '', bank_name: '', branch: ''})
  const [ratePlanData, setRatePlanData] = useState({plan_type: '', amount: '', valid_from: '', valid_to: '', working_day_mode: '', project_id: ''})
  const [appointmentText, setAppointmentText] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchPerson()
  }, [personId])

  const fetchPerson = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Person>(`/persons/${personId}`)
      if (response.data) {
        setPerson(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch person')
    } finally {
      setLoading(false)
    }
  }

  const handleAssignEmployment = async () => {
    setSaving(true)
    try {
      const response = await apiRequest(`/finance/persons/${personId}/assign`, {
        method: 'POST',
        body: JSON.stringify(employmentData),
      })
      if (response.data) {
        fetchPerson()
        alert('Employment assigned successfully! Employee code generated.')
      }
    } catch (err) {
      alert('Failed to assign employment')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveKYC = async () => {
    setSaving(true)
    try {
      const response = await apiRequest(`/finance/persons/${personId}/kyc`, {
        method: 'POST',
        body: JSON.stringify(kycData),
      })
      if (response.data) {
        alert('KYC saved successfully!')
      }
    } catch (err) {
      alert('Failed to save KYC')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveRatePlan = async () => {
    setSaving(true)
    try {
      // FIXED: Clean up empty strings and convert to proper types
      const cleanedData: any = {
        plan_type: ratePlanData.plan_type || undefined,
        amount: ratePlanData.amount ? parseFloat(ratePlanData.amount) : undefined,
        valid_from: ratePlanData.valid_from || undefined,
        valid_to: ratePlanData.valid_to || null,
        working_day_mode: ratePlanData.working_day_mode || null,
        project_id: ratePlanData.project_id ? parseInt(ratePlanData.project_id) : null,
      }
      
      // Remove undefined fields
      Object.keys(cleanedData).forEach(key => {
        if (cleanedData[key] === undefined) {
          delete cleanedData[key]
        }
      })
      
      const response = await apiRequest(`/finance/persons/${personId}/rate-plan`, {
        method: 'POST',
        body: JSON.stringify(cleanedData),
      })
      
      if (response.error) {
        alert(`Failed to save rate plan: ${response.error}`)
        return
      }
      
      if (response.data) {
        alert('Rate plan saved successfully!')
        fetchPerson() // Refresh person data
      }
    } catch (err: any) {
      console.error('Rate plan save error:', err)
      alert(`Failed to save rate plan: ${err?.message || 'Unknown error'}`)
    } finally {
      setSaving(false)
    }
  }

  const handleSubmitToHR = async () => {
    try {
      const response = await apiRequest(`/finance/persons/${personId}/submit-to-hr`, {
        method: 'POST',
      })
      if (response.data) {
        alert('Submitted to HR successfully!')
        router.push('/tickets')
      }
    } catch (err) {
      alert('Failed to submit to HR')
    }
  }

  const handleGenerateDeclaration = async () => {
    try {
      const response = await apiRequest(`/hr/persons/${personId}/generate-declaration`, {
        method: 'POST',
      })
      if (response.data) {
        alert('Declaration generated!')
      }
    } catch (err) {
      alert('Failed to generate declaration')
    }
  }

  const handleGenerateAppointment = async () => {
    try {
      const response = await apiRequest<{draft_text: string}>(`/hr/persons/${personId}/generate-appointment`, {
        method: 'POST',
      })
      if (response.data) {
        setAppointmentText(response.data.draft_text)
      }
    } catch (err) {
      alert('Failed to generate appointment')
    }
  }

  const handleSaveAppointment = async () => {
    try {
      const response = await apiRequest(`/hr/persons/${personId}/appointment`, {
        method: 'PATCH',
        body: JSON.stringify({appointment_text: appointmentText}),
      })
      if (response.data) {
        alert('Appointment saved!')
      }
    } catch (err) {
      alert('Failed to save appointment')
    }
  }

  const handleMarkActive = async () => {
    try {
      const response = await apiRequest(`/hr/persons/${personId}/mark-active`, {
        method: 'POST',
      })
      if (response.data) {
        alert('Person marked as active!')
        router.push('/tickets')
      }
    } catch (err) {
      alert('Failed to mark as active')
    }
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <UserShell>
          <div className="p-6">Loading...</div>
        </UserShell>
      </ProtectedRoute>
    )
  }

  if (!person) {
    return (
      <ProtectedRoute>
        <UserShell>
          <div className="p-6">Person not found</div>
        </UserShell>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <UserShell>
        <div className="p-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>{person.name}</CardTitle>
                  <CardDescription>
                    {person.email} | {person.mobile}
                    {person.employee_code && ` | ${person.employee_code}`}
                  </CardDescription>
                </div>
                <Badge variant="secondary">{person.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={(v) => router.push(`/persons/${personId}?tab=${v}`)}>
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="finance">Finance</TabsTrigger>
                  <TabsTrigger value="hr">HR</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="mt-4">
                  <div className="space-y-4">
                    <div>
                      <Label>Name</Label>
                      <p className="text-sm">{person.name}</p>
                    </div>
                    <div>
                      <Label>Mobile</Label>
                      <p className="text-sm">{person.mobile}</p>
                    </div>
                    <div>
                      <Label>Email</Label>
                      <p className="text-sm">{person.email || '-'}</p>
                    </div>
                    <div>
                      <Label>Status</Label>
                      <p className="text-sm">{person.status}</p>
                    </div>
                    {person.employee_code && (
                      <div>
                        <Label>Employee Code</Label>
                        <p className="text-sm">{person.employee_code}</p>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="finance" className="mt-4">
                  <div className="space-y-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Assign Employment</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <Label htmlFor="employment_type">Employment Type</Label>
                          <select
                            id="employment_type"
                            value={employmentData.employment_type}
                            onChange={(e) => setEmploymentData({...employmentData, employment_type: e.target.value})}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          >
                            <option value="">Select Type</option>
                            <option value="PERMANENT">PERMANENT</option>
                            <option value="FREELANCER">FREELANCER</option>
                            <option value="CONTRACTUAL">CONTRACTUAL</option>
                          </select>
                        </div>
                        <div>
                          <Label htmlFor="company_id">Company</Label>
                          <Input
                            id="company_id"
                            type="number"
                            value={employmentData.company_id}
                            onChange={(e) => setEmploymentData({...employmentData, company_id: e.target.value})}
                            placeholder="Company ID"
                          />
                        </div>
                        <Button onClick={handleAssignEmployment} disabled={saving}>
                          {saving ? 'Assigning...' : 'Assign & Generate Code'}
                        </Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Finance KYC</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="aadhaar">Aadhaar</Label>
                            <Input
                              id="aadhaar"
                              value={kycData.aadhaar}
                              onChange={(e) => setKycData({...kycData, aadhaar: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="pan">PAN</Label>
                            <Input
                              id="pan"
                              value={kycData.pan}
                              onChange={(e) => setKycData({...kycData, pan: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="bank_account_no">Bank Account No</Label>
                            <Input
                              id="bank_account_no"
                              value={kycData.bank_account_no}
                              onChange={(e) => setKycData({...kycData, bank_account_no: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="ifsc">IFSC</Label>
                            <Input
                              id="ifsc"
                              value={kycData.ifsc}
                              onChange={(e) => setKycData({...kycData, ifsc: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="bank_name">Bank Name</Label>
                            <Input
                              id="bank_name"
                              value={kycData.bank_name}
                              onChange={(e) => setKycData({...kycData, bank_name: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="branch">Branch</Label>
                            <Input
                              id="branch"
                              value={kycData.branch}
                              onChange={(e) => setKycData({...kycData, branch: e.target.value})}
                            />
                          </div>
                        </div>
                        <Button onClick={handleSaveKYC} disabled={saving}>
                          <Save className="w-4 h-4 mr-2" />
                          Save KYC
                        </Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Rate Plan</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="plan_type">Plan Type</Label>
                            <select
                              id="plan_type"
                              value={ratePlanData.plan_type}
                              onChange={(e) => setRatePlanData({...ratePlanData, plan_type: e.target.value})}
                              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            >
                              <option value="">Select Type</option>
                              <option value="MANDAY">MANDAY</option>
                              <option value="MANMONTH">MANMONTH</option>
                              <option value="MONTHLY_SALARY">MONTHLY_SALARY</option>
                            </select>
                          </div>
                          <div>
                            <Label htmlFor="amount">Amount</Label>
                            <Input
                              id="amount"
                              type="number"
                              value={ratePlanData.amount}
                              onChange={(e) => setRatePlanData({...ratePlanData, amount: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="valid_from">Valid From</Label>
                            <Input
                              id="valid_from"
                              type="date"
                              value={ratePlanData.valid_from}
                              onChange={(e) => setRatePlanData({...ratePlanData, valid_from: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="valid_to">Valid To</Label>
                            <Input
                              id="valid_to"
                              type="date"
                              value={ratePlanData.valid_to}
                              onChange={(e) => setRatePlanData({...ratePlanData, valid_to: e.target.value})}
                            />
                          </div>
                        </div>
                        <Button onClick={handleSaveRatePlan} disabled={saving}>
                          <Save className="w-4 h-4 mr-2" />
                          Save Rate Plan
                        </Button>
                      </CardContent>
                    </Card>

                    <Button onClick={handleSubmitToHR} className="w-full" size="lg">
                      Submit to HR
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="hr" className="mt-4">
                  <div className="space-y-6">
                    <HRDocumentsPanel personId={personId} />

                    <Card>
                      <CardHeader>
                        <CardTitle>Actions</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Button onClick={handleMarkActive} className="w-full" size="lg">
                          <Check className="w-4 h-4 mr-2" />
                          Mark as Active
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </UserShell>
    </ProtectedRoute>
  )
}

