"""
Seed DECLARATION template so HR Documents shows Declaration as Available.
Run this if the UI shows "Declaration: Missing Template".

Usage (from repo root; ensure .env is loaded or set DATABASE_URL):
  python backend/scripts/seed_declaration_template.py

Or from backend/ (with .env in backend/ or parent):
  python scripts/seed_declaration_template.py

Ensures:
- A Template row with type=DECLARATION exists.
- A TemplateRevision with status=PUBLISHED exists and is set as active_revision_id.
- If template existed but had no published revision, adds one with ACS default content.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.template import Template, TemplateRevision, TemplateType, RevisionStatus
from app.models.user import User

# ACS Declaration default content (keep in sync with seed_appointment_template.DECLARATION_TEMPLATE_HTML)
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


def seed_declaration():
    db = SessionLocal()
    try:
        admin_user = db.query(User).first()
        if not admin_user:
            print("No user found. Create a user first (e.g. run app or seed users).")
            return False

        template = db.query(Template).filter(Template.type == TemplateType.DECLARATION).first()
        if not template:
            template = Template(type=TemplateType.DECLARATION)
            db.add(template)
            db.flush()
            print("Created Template with type=DECLARATION.")

        # Check for any published revision
        published = db.query(TemplateRevision).filter(
            TemplateRevision.template_id == template.id,
            TemplateRevision.status == RevisionStatus.PUBLISHED
        ).order_by(TemplateRevision.created_at.desc()).first()

        if published:
            if template.active_revision_id != published.id:
                template.active_revision_id = published.id
                db.commit()
                print("DECLARATION template already has a published revision; set as active.")
            else:
                print("DECLARATION template already seeded (published revision active).")
            return True

        # No published revision: create one
        revision = TemplateRevision(
            template_id=template.id,
            version="1.0.0",
            content=DECLARATION_TEMPLATE_HTML,
            status=RevisionStatus.PUBLISHED,
            created_by=admin_user.id
        )
        db.add(revision)
        db.flush()
        template.active_revision_id = revision.id
        template.is_active = True
        for t in db.query(Template).filter(Template.type == TemplateType.DECLARATION).all():
            t.is_active = t.id == template.id
        db.commit()
        print("Created DECLARATION template revision 1.0.0 (PUBLISHED) and set as active.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_declaration()
