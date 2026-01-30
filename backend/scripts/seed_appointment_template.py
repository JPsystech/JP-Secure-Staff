"""Seed initial Appointment Letter template"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.template import Template, TemplateRevision, TemplateType, RevisionStatus
from app.models.user import User

APPOINTMENT_TEMPLATE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Appointment Letter - {{person.name}}</title>
  <style>
    @page { size: A4; margin: 18mm 16mm; }
    * { box-sizing: border-box; }
    body {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 12.2px;
      line-height: 1.45;
      color: #111;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 10px;
      margin-bottom: 12px;
    }
    .brand {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .logo {
      width: 44px;
      height: 44px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
    }
    .logo img { width: 100%; height: 100%; object-fit: contain; }
    .brand h1 {
      font-size: 16px;
      margin: 0;
      line-height: 1.2;
    }
    .brand .sub {
      font-size: 11px;
      color: #4b5563;
      margin-top: 2px;
    }
    .meta {
      text-align: right;
      font-size: 11.5px;
      color: #111;
    }
    .meta .muted { color: #6b7280; }
    h2 {
      font-size: 14px;
      margin: 10px 0 6px;
    }
    .to-block { margin-top: 10px; }
    .to-block p { margin: 2px 0; }
    .title {
      margin-top: 10px;
      padding: 10px 12px;
      background: #f8fafc;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
    }
    .title h2 { margin: 0; }
    .section {
      margin-top: 12px;
    }
    .info-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      overflow: hidden;
    }
    .info-table td {
      padding: 8px 10px;
      border-bottom: 1px solid #e5e7eb;
      vertical-align: top;
    }
    .info-table tr:last-child td { border-bottom: none; }
    .label {
      width: 32%;
      color: #374151;
      background: #f9fafb;
      font-weight: 600;
    }
    ul { margin: 6px 0 0 18px; }
    li { margin: 6px 0; }
    .note {
      margin-top: 10px;
      padding: 10px 12px;
      border-left: 3px solid #111827;
      background: #f9fafb;
      color: #111;
      border-radius: 8px;
    }
    .footer {
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
    }
    .sign {
      width: 48%;
    }
    .sign .line {
      margin-top: 26px;
      border-top: 1px solid #111;
      padding-top: 6px;
      font-size: 11.5px;
    }
    .small { font-size: 11px; color: #374151; }
    .page-break { page-break-before: always; }
    .web { color: #111; text-decoration: none; }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">
      <div class="logo">
        {{#if company.logoUrl}}
          <img src="{{company.logoUrl}}" alt="{{company.name}} Logo" />
        {{else}}
          <span style="font-size:10px;color:#6b7280;">LOGO</span>
        {{/if}}
      </div>
      <div>
        <h1>{{company.name}}</h1>
        <div class="sub">{{company.tagline}}</div>
      </div>
    </div>
    <div class="meta">
      <div><span class="muted">Reference No:</span> <strong>{{letter.referenceNo}}</strong></div>
      <div><span class="muted">Date:</span> <strong>{{letter.date}}</strong></div>
    </div>
  </div>
  <div class="to-block">
    <p><strong>To:</strong></p>
    <p><strong>{{person.name}}</strong></p>
    <p>Mobile: {{person.mobile}}</p>
    <p>E-mail: {{person.email}}</p>
  </div>
  <div class="title">
    <h2>{{letter.subject}}</h2>
  </div>
  <div class="section">
    <p>
      Welcome, <strong>{{person.name}}</strong>. We are pleased to offer you the position of
      <strong>{{job.title}}</strong> at <strong>{{company.name}}</strong>.
      Your employment with {{company.name}} is subject to a probation period of
      <strong>{{job.probationMonths}}</strong> months, which may be extended for another
      <strong>{{job.probationExtensionMonths}}</strong> months based on your performance.
    </p>
    <p>
      If agreed, you should return the duly signed copy as acceptance by
      <strong>{{job.acceptanceDeadline}}</strong> from receipt of this offer letter, along with
      self-attested copies of credentials through mail (scan copy) at <strong>{{company.hrEmail}}</strong>
      and also via courier/registered post/by hand at the address below.
    </p>
    <table class="info-table">
      <tr>
        <td class="label">Reporting Address</td>
        <td>{{job.reportingAddress}}</td>
      </tr>
      <tr>
        <td class="label">Reporting Date</td>
        <td>{{job.reportingDate}}</td>
      </tr>
      <tr>
        <td class="label">Compensation</td>
        <td>
          <div><strong>{{job.salaryDuringProbation}}</strong> INR per month (fixed).</div>
          <div class="small" style="margin-top:6px;">
            After the probation period, your expected compensation of <strong>{{job.salaryAfterProbation}}</strong>
            INR will be considered for review, subject to your performance during this period.
          </div>
        </td>
      </tr>
      <tr>
        <td class="label">HR Contact</td>
        <td>
          For any query, please contact only HR Dept. on:
          <strong>{{company.hrPhones}}</strong>
        </td>
      </tr>
    </table>
    <div class="note">
      Please consider this letter strictly confidential. Do not disclose the specific details to anyone,
      including compensation amount. Otherwise, disciplinary action may be taken, which may lead to termination.
    </div>
    <p style="margin-top:10px;">
      The appointment is subject to the following terms and conditions:
    </p>
    <ul>
      <li><strong>Initial Posting Location:</strong> You will initially be based in {{job.initialPostingLocation}}. However, {{company.name}} reserves the right to transfer you to any other location as required.</li>
      <li><strong>Travel Requirements:</strong> You may be required to travel as per operational needs.</li>
      <li><strong>Documentation:</strong> Your resume and documents submitted are assumed to be accurate. Any discrepancies may result in termination of employment.</li>
      <li><strong>Working Hours:</strong> You may be required to work beyond normal working hours as per business requirement and you will not be eligible for any overtime payment.</li>
      <li><strong>Office Working Schedule:</strong> Office timing is {{policy.officeStartTime}} to {{policy.officeEndTime}} ({{policy.weeklyOff}} off). Break time {{policy.breakStart}} to {{policy.breakEnd}}.</li>
      <li><strong>Leave Policy:</strong> Leave during probation is not allowed unless there is a medical emergency or other emergency; {{company.name}} reserves the right to approve/reject leave.</li>
      <li><strong>Confidentiality:</strong> You shall not disclose confidential information, internal documents, policies, procedures, client details, or proprietary information of {{company.name}} to any third party.</li>
      <li><strong>Code of Conduct:</strong> You shall maintain discipline, integrity, and comply with company rules and policies at all times.</li>
      <li><strong>Non-Solicitation:</strong> You agree not to establish personal contacts with clients for purposes outside designated responsibilities. During employment, you shall refrain from applying for client jobs. For {{policy.postTerminationMonths}} months after termination, you shall not seek or accept employment with any client company where you were deputed.</li>
      <li><strong>Dispute Resolution:</strong> Disputes will be resolved through arbitration as per the Arbitration and Conciliation Act, 1996. Arbitrator decision shall be final and binding.</li>
      <li><strong>Applicable Law & Jurisdiction:</strong> This contract is governed by laws of India and subject to jurisdiction of courts in {{policy.jurisdictionCity}}, {{policy.jurisdictionState}}.</li>
      <li><strong>Return of Property:</strong> On termination, you must return all company property (physical and electronic). For lost/damaged property, you must compensate at current market rate.</li>
      <li><strong>Termination of Contract:</strong> Contract may be terminated by either party with {{policy.noticeDays}} days prior written notice. Appointee must complete ongoing work and cannot terminate mid-way. {{company.name}} reserves right to terminate immediately for misconduct, breach, confidentiality violation, or acts detrimental to company interests.</li>
      <li><strong>No-Due & Clearance:</strong> Before final release, you must obtain No-Due and Clearance Certificates from each department.</li>
    </ul>
    <p style="margin-top:10px;">
      By signing below, I confirm that I have read, understood, and agree to the terms and conditions and will comply with restrictions outlined in this appointment letter.
    </p>
    <p style="margin-top:14px;">
      Best Regards,<br/>
      <strong>HR Department</strong><br/>
      {{company.name}}<br/>
      {{company.hrEmail}}
    </p>
    <h2>Declaration:</h2>
    <p>
      I hereby unconditionally accept the above appointment on the terms and conditions mentioned herein and agree to abide by them.
      Further, I have read and understood the contents of this appointment letter and will comply with the same.
    </p>
    <div class="footer">
      <div class="sign">
        <div class="line">Employee Signature</div>
        <div class="small">Name: {{person.name}}</div>
        <div class="small">Date: {{letter.employeeSignDate}}</div>
      </div>
      <div class="sign">
        <div class="line">Authorized Signatory</div>
        <div class="small">{{company.name}}</div>
        <div class="small">Date: {{letter.date}}</div>
      </div>
    </div>
    <p class="small" style="margin-top:14px;">
      Website: <a class="web" href="{{company.website}}">{{company.website}}</a>
    </p>
  </div>
</body>
</html>"""

# ACS Declaration format – default template content (Handlebars placeholders)
DECLARATION_TEMPLATE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Declaration - {{person.name}}</title>
  <style>
    @page { size: A4; margin: 18mm 16mm; }
    * { box-sizing: border-box; }
    body { font-family: Arial, Helvetica, sans-serif; font-size: 12px; line-height: 1.5; color: #111; }
    .header { border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 12px; }
    .brand h1 { font-size: 16px; margin: 0; }
    .brand .sub { font-size: 11px; color: #4b5563; }
    .meta { font-size: 11px; color: #6b7280; margin-top: 4px; }
    h2 { font-size: 14px; margin: 12px 0 8px; text-align: center; }
    .section { margin-top: 12px; }
    .section p { margin: 8px 0; }
    ul { margin: 8px 0 0 20px; }
    li { margin: 4px 0; }
    .footer { margin-top: 24px; }
    .sign-block { margin-top: 20px; border-top: 1px solid #111; padding-top: 8px; font-size: 11px; }
    .sign-block.uppercase { text-transform: uppercase; }
    .website { margin-top: 16px; font-size: 11px; color: #6b7280; text-align: center; }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">
      <h1>{{company.name}}</h1>
      <div class="sub">(ACS) – Address and contact from company config</div>
    </div>
    <div class="meta">Ref: {{letter.referenceNo}} | Date: {{letter.date}} | Emp Code: {{person.emp_code}}</div>
  </div>
  <h2>DECLARATION</h2>
  <div class="section">
    <p>I, <strong>{{person.name}}</strong> working as a Freelancer/Consultant, hereby declare that I am engaged under the scope of work assigned by {{company.name}}.</p>
    <p>I undertake to strictly comply with all applicable Government Acts, Rules, and Regulations, including but not limited to:</p>
    <ul>
      <li>The Factories Act, 1948</li>
      <li>The Building and Other Construction Workers (Regulation of Employment and Conditions of Service) Act, 1996</li>
      <li>The Occupational Safety, Health and Working Conditions Code, 2020</li>
      <li>The Environment (Protection) Act, 1986</li>
      <li>And all other relevant Central and State laws concerning Safety, Health, and Environmental Protection.</li>
    </ul>
    <p>I further declare that I will:</p>
    <ol>
      <li>Follow all safety precautions and PPE requirements during the execution of my duties.</li>
      <li>Adhere to all client site safety procedures, instructions, and permit systems.</li>
      <li>Not engage in any unsafe practices or unauthorized activities at the worksite.</li>
      <li>Immediately report any unsafe condition, near miss, or incident to the client's safety department.</li>
    </ol>
    <p>I fully understand that {{company.name}} shall not be responsible or liable for any accident, injury, damage, or incident occurring during my working period, whether at the client's premises, during travel, or at any related location. All such risks, responsibilities, and liabilities shall be borne solely by me as an independent freelancer/consultant.</p>
    <p>This declaration is made voluntarily and in full compliance with Government safety regulations and client site requirements.</p>
  </div>
  <div class="footer">
    <div class="sign-block uppercase">Freelancer Name: {{person.name_upper}}</div>
    <div class="sign-block">Signature: ___________________   Date: {{letter.todayDateDDMMYYYY}}</div>
    <div class="sign-block">Witness (ACS Representative): {{letter.acsWitnessName}}</div>
    <div class="sign-block">Witness Signature: ____________   Date: {{letter.todayDateDDMMYYYY}}</div>
  </div>
  {{#if company.website}}
  <div class="website">{{company.website}}</div>
  {{/if}}
</body>
</html>"""

def seed_templates():
    db = SessionLocal()
    try:
        # Get admin user (first user or create a system user)
        admin_user = db.query(User).first()
        if not admin_user:
            print("No admin user found. Please create a user first.")
            return
        
        # Create templates for each type
        template_types = [
            TemplateType.APPOINTMENT_PERMANENT,
            TemplateType.APPOINTMENT_FREELANCER,
            TemplateType.APPOINTMENT_CONTRACTUAL,
            TemplateType.DECLARATION
        ]
        
        for template_type in template_types:
            # Check if template already exists
            existing = db.query(Template).filter(Template.type == template_type).first()
            if existing:
                print(f"Template {template_type.value} already exists, skipping...")
                continue
            
            # Create template
            template = Template(type=template_type)
            db.add(template)
            db.flush()
            
            # Create initial revision with content
            if template_type == TemplateType.DECLARATION:
                content = DECLARATION_TEMPLATE_HTML
            else:
                content = APPOINTMENT_TEMPLATE_HTML
            
            revision = TemplateRevision(
                template_id=template.id,
                version="1.0.0",
                content=content,
                status=RevisionStatus.PUBLISHED,
                created_by=admin_user.id
            )
            db.add(revision)
            db.flush()
            
            # Set as active revision
            template.active_revision_id = revision.id
            db.commit()
            
            print(f"Created template {template_type.value} with revision 1.0.0 (PUBLISHED)")
        
        print("Template seeding completed!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding templates: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_templates()

