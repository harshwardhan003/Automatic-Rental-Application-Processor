"""
RPA Module: Email Templates
Contains all templated email strings for the DRAP system.
"""

MISSING_DOCS_TEMPLATE = """Subject: Application Ref {ref_number} — Action Required: Missing Documents

Dear {applicant_name},

Thank you for your rental application for {property_address} (Reference: {ref_number}).

We are unable to process your application as the following required document(s) were missing:

{missing_docs_list}

Please resubmit these within 48 hours to remain in consideration.

Kind regards,
Clarendon Residential
"""

INCOME_REJECTION_TEMPLATE = """Subject: Application Ref {ref_number} — Outcome: Unsuccessful

Dear {applicant_name},

Thank you for your interest in {property_address}.

Unfortunately, we cannot progress your application as the property requires a minimum income of €{required_income:,.0f} per month (3x rent coverage), which your documentation did not meet.

We wish you the best in your search.

Kind regards,
Clarendon Residential
"""

VIEWING_INVITATION_TEMPLATE = """Subject: Application Ref {ref_number} — Invitation to Viewing ✓

Dear {applicant_name},

Congratulations! Your application for {property_address} has been shortlisted.

We were particularly impressed with your application. Our assessment noted:
"{transparency_note}"

We would like to invite you to a viewing this Thursday between 5:00 PM and 7:00 PM. Please reply to this email to confirm your attendance.

Kind regards,
Siobhán Ní Bhriain
Clarendon Residential
"""

AI_REJECTION_TEMPLATE = """Subject: Application Ref {ref_number} — Outcome: Unsuccessful

Dear {applicant_name},

Thank you for your application for {property_address}.

After a detailed assessment of all submitted documents and references, we regret to inform you that we will not be moving forward with your application at this time.

Transparent Feedback:
Our assessment identified the following areas where the application did not meet our current requirements:
- {transparency_note}

Due to the extremely high volume of applications, we are prioritizing candidates who more closely align with the landlord's specific criteria for this tenancy.

We wish you every success in finding a suitable home.

Kind regards,
Siobhán Ní Bhriain
Clarendon Residential
"""

ACKNOWLEDGEMENT_TEMPLATE = """Subject: Application Ref {ref_number} — Received Successfully ✓

Dear {applicant_name},

Thank you for your application for {property_address}. Your reference number is {ref_number}.

Your application is now being assessed and we will contact you with a decision shortly.

Kind regards,
Clarendon Residential
"""
