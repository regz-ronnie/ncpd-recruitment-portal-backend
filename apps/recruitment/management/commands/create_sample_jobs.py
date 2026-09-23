from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.recruitment.models import JobPost, JobCategory
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create NCPD job postings from vacancies advertisement'

    def handle(self, *args, **options):
        # Create job categories
        programme_mgmt, _ = JobCategory.objects.get_or_create(
            name='Programme Management',
            defaults={'description': 'Population programme management roles'}
        )
        
        planning_research, _ = JobCategory.objects.get_or_create(
            name='Planning and Research',
            defaults={'description': 'Planning and research roles'}
        )
        
        leadership, _ = JobCategory.objects.get_or_create(
            name='Leadership',
            defaults={'description': 'Senior leadership positions'}
        )
        
        corporate_services, _ = JobCategory.objects.get_or_create(
            name='Corporate Services',
            defaults={'description': 'Finance, HR, Administration, ICT roles'}
        )
        
        ict, _ = JobCategory.objects.get_or_create(
            name='ICT',
            defaults={'description': 'Information and Communication Technology roles'}
        )
        
        operations, _ = JobCategory.objects.get_or_create(
            name='Operations',
            defaults={'description': 'Support and operational roles'}
        )
        
        # Get or create a default user for posted_by
        default_user, _ = User.objects.get_or_create(
            email='admin@ncpd.go.ke',
            defaults={
                'username': 'admin@ncpd.go.ke',
                'first_name': 'NCPD',
                'last_name': 'Admin',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # NCPD Vacancies Advertisement Data
        jobs_data = [
            {
                'title': 'DIRECTOR POLICY, PROGRAMMES AND PARTNERSHIP – GRADE NCPD 2',
                'description': 'Responsible for development, implementation and review of population policies, programmes and foster partnerships at national and county levels. Reports to the Director General.',
                'requirements': '''For appointment to this grade, a candidate must have:
- Satisfactorily served for a cumulative period of fifteen years, three of which should have been at least at the level of Assistant Director of Population, Grade NCPD 4 or an equivalent position in a comparable organization
- Master's Degree in any of the following disciplines: Population Studies, Demography, Public Health, Sociology, Anthropology, Geography, Economics, Population Health or Political Science from a recognized institution
- Bachelor's Degree in any of the following disciplines: Population Studies, Demography, Public Health, Sociology, Anthropology, Geography, Economics, Population Health, Political Science or equivalent qualification from a recognized institution
- Leadership and Management Course Certificate from a recognized institution
- Membership to a relevant professional body
- Proficiency in Computer applications skills
- Demonstrated managerial and administrative capability and professional competence in work performance and results
- Exhibited a thorough understanding of national goals, policies, objectives and ability to relate them to NCPDs mandate
- Fulfilled the requirements of Chapter Six of the Constitution''',
                'responsibilities': '''The job entails the following:
- Overseeing the development, implementation and review of population policies, programme guidelines and standards
- Coordinating the development of institutional frameworks and strategies for population policies and programmes at the national, sectoral and county levels
- Coordinating integration of population issues into the National and County Development Plans
- Spearheading the alignment of the National Population Policy with other related national, international, regional policies and frameworks
- Overseeing the development of reports, position papers, cabinet memos and briefs on population and development issues
- Coordinating the implementation of population programmes/projects at national and county levels
- Coordinating the stakeholders implementing population and development programmes and projects and strengthening partnerships and collaborations at national and county levels
- Coordinating, development and implementation of national, regional and international population programmes, plans and strategies
- Coordinating resource mobilization activities for implementation of population programmes and projects''',
                'qualifications': [
                    '15 years cumulative experience, 3 years at Assistant Director level',
                    'Masters in Population Studies, Demography, Public Health, Sociology, Anthropology, Geography, Economics, Population Health or Political Science',
                    'Bachelors in related field',
                    'Leadership and Management Course Certificate',
                    'Professional body membership',
                    'Computer proficiency',
                    'Chapter Six compliance'
                ],
                'category': leadership,
                'department': 'Policy, Programmes and Partnership',
                'location': 'Nairobi',
                'county': 'Nairobi',
                'employment_type': 'contract',
                'application_deadline': timezone.now() + timedelta(days=30),
                'status': 'published',
                'is_featured': True,
                'is_urgent': True,
                'max_applications': 50,
                'auto_screening': True,
                'require_cover_letter': True,
                'posted_by': default_user,
            },
            {
                'title': 'DIRECTOR CORPORATE SERVICES – GRADE NCPD 2',
                'description': 'Oversee the finance & accounts, human resources & administration, planning & strategy and information communication technology functions at the Council. Reports to the Director General.',
                'requirements': '''For appointment to this grade, an officer must have:
- Satisfactorily served for a cumulative period of fifteen years, three of which should have been at the level of Assistant Director level, Grade NCPD 4 and above or an equivalent position in a comparable organization
- Master's degree in any of the following disciplines: Human Resource Management, Public Administration, Commerce (Accounting/Finance Option), Finance, Economics, Business Administration/Management or equivalent qualification from a recognized institution
- Bachelor's degree in any of the following disciplines: Human Resource Management, Public Administration, Commerce (Accounting/Finance Option), Finance, Economics, Business Management/Administration, Public Administration or equivalent qualification from a recognized institution
- Leadership and Management Course Certificate from a recognized institution
- Membership to a relevant professional body
- Proficiency in computer applications
- Demonstrated managerial, administrative and professional competence in work performance and results
- Exhibited a thorough understanding of national goals, policies, objectives and ability to relate them to NCPDs mandate
- Fulfilled the requirements of Chapter Six of the Constitution''',
                'responsibilities': '''The job entails the following:
- Coordinating development, implementation and review of finance, accounts, human resource management, administration, ICT, policies and procedures
- Providing strategic leadership and direction in the performance of the finance, accounts, planning and strategy, human resource management, administration, ICT and records management functions
- Spearheading analysis of the Councils finance, accounts, human resource management, administration, ICT and records management structures and systems and recommending areas of improvement
- Overseeing staff performance management and improvement strategies in the directorate
- Steer the preparation and implementation of the Council's corporate services budgets
- Provide leadership in the Council's compliance to statutory requirements
- Managing NCPD's assets and liabilities register
- Overseeing the budgeting and implementation of activities in the directorate''',
                'qualifications': [
                    '15 years cumulative experience, 3 years at Assistant Director level',
                    'Masters in HRM, Public Admin, Commerce, Finance, Economics, Business Admin',
                    'Bachelors in related field',
                    'Leadership and Management Course Certificate',
                    'Professional body membership',
                    'Computer proficiency',
                    'Chapter Six compliance'
                ],
                'category': corporate_services,
                'department': 'Corporate Services',
                'location': 'Nairobi',
                'county': 'Nairobi',
                'employment_type': 'contract',
                'application_deadline': timezone.now() + timedelta(days=30),
                'status': 'published',
                'is_featured': True,
                'is_urgent': True,
                'max_applications': 50,
                'auto_screening': True,
                'require_cover_letter': True,
                'posted_by': default_user,
            },
            {
                'title': 'PRINCIPAL ICT OFFICER – GRADE NCPD 5',
                'description': 'Responsible for deployment of ICT infrastructure, systems and related applications; advising on electronic systems controls to support business operations and realization of the Councils mandate. Reports to Deputy Director/Assistant Director ICT.',
                'requirements': '''For appointment to this grade, an officer must have:
- Satisfactorily served for a cumulative period of nine years, three of which should have been at Senior ICT Officer level, Grade NCPD 6 or an equivalent position in a comparable organization
- Bachelor's degree in any of the following disciplines: Graphic Design, Computer Science, Information Technology, Business Information Technology or equivalent qualification from recognized institution
- Certification in MOUS/A+/N+/Linux and any of the following: Relational Database Management, Software Development, Systems Security or equivalent and relevant qualification from a recognized institution
- Certificate in Management Course from a recognized institution
- Membership to a relevant professional body where applicable
- Demonstrated merit and ability as reflected in work performance and results
- Fulfilled the requirements of Chapter Six of the Constitution''',
                'responsibilities': '''The job entails the following:
- Coordinating computer network access and use
- Coordinating the implementation of network security measures
- Establishing appropriate operational procedures, tools and resources
- Testing and reviewing enhancements of new software
- Ensuring designing, maintenance, management and development of the NCPD network infrastructure, associated network services, platform infrastructure and core ICT business services
- Providing technical and operational support for systems and infrastructure, including networks, servers, website, email, ERP, database and other NCPD ICT related applications
- Providing cross discipline third level operational infrastructure coordination, monitoring, support and enhancement to enterprise infrastructure service delivery
- Managing incidents and service requests requiring third level support logged by customers through the NCPD helpdesk
- Managing infrastructure generated incidents''',
                'qualifications': [
                    '9 years cumulative experience, 3 years at Senior ICT Officer level',
                    'Bachelors in Graphic Design, Computer Science, IT, Business IT',
                    'MOUS/A+/N+/Linux certification',
                    'Database/Software Development/Systems Security certification',
                    'Management Course Certificate',
                    'Professional body membership',
                    'Chapter Six compliance'
                ],
                'category': ict,
                'department': 'ICT',
                'location': 'Nairobi',
                'county': 'Nairobi',
                'employment_type': 'full_time',
                'application_deadline': timezone.now() + timedelta(days=30),
                'status': 'published',
                'max_applications': 30,
                'auto_screening': True,
                'require_cover_letter': True,
                'posted_by': default_user,
            },
            {
                'title': 'DRIVER II – GRADE NCPD 10',
                'description': 'Driving the vehicle as authorized, ensuring security and safety of the vehicle, passengers and goods on and off the road.',
                'requirements': '''For appointment to this grade, a candidate must have:
- Satisfactorily served for a cumulative period of six (6) years, three of which should have been at Driver II, Grade NCPD 10, or an equivalent position in a comparable organization for a minimum of three years
- Minimum mean grade of KCSE Grade D or its equivalent
- Valid Class BCE Driving License free from any endorsement
- Occupational Test Grade II Certificate for Drivers and Defensive Driving Certificate or its equivalent qualification from a recognized and accredited institution
- First-Aid Certificate Course lasting not less than one (1) week from St. John Ambulance or Kenya Institute of Highways and Building Technology (KIHBT) or any other recognized and accredited institution
- Demonstrated outstanding professional competence, good conduct, and respect and integrity in work performance
- Basic mechanical skills and knowledge will be an added advantage
- Fulfilled the requirements of Chapter Six of the Constitution''',
                'responsibilities': '''The job entails the following:
- Driving the vehicle as authorized
- Ensuring security and safety of the vehicle, passengers and goods on and off the road
- Maintaining daily work ticket
- Carrying out routine checks on vehicle's cooling, oil, electrical and brake systems and tyre pressure
- Detecting and reporting vehicle defects on time
- Ensuring vehicle cleanliness
- Reporting accidents promptly and following up on police abstracts
- Inspecting vehicles and keeping up-to-date insurance documents''',
                'qualifications': [
                    '6 years cumulative experience, 3 years at Driver II level',
                    'KCSE Grade D or equivalent',
                    'Class BCE Driving License',
                    'Occupational Test Grade II Certificate',
                    'Defensive Driving Certificate',
                    'First-Aid Certificate',
                    'Basic mechanical skills advantage',
                    'Chapter Six compliance'
                ],
                'category': operations,
                'department': 'Operations',
                'location': 'Nairobi',
                'county': 'Nairobi',
                'employment_type': 'full_time',
                'application_deadline': timezone.now() + timedelta(days=30),
                'status': 'published',
                'max_applications': 100,
                'auto_screening': True,
                'require_cover_letter': False,
                'posted_by': default_user,
            },
            {
                'title': 'CUSTOMER CARE ASSISTANT III – GRADE NCPD 10',
                'description': 'Operating the switchboard and all exchange equipment within the Council to ensure smooth flow of communication and operation.',
                'requirements': '''For appointment to this grade, an officer must have:
- Certificate in any of the following disciplines: Mass Communications, Customer Care, Public Relations or equivalent qualification from a recognized institution
- Minimum mean grade of KCSE D or its equivalent
- Proficiency in Computer application skills''',
                'responsibilities': '''The job entails the following:
- Operating the switchboard and all exchange equipment within the Council to ensure smooth flow of communication and operation
- Controlling access to clients visiting the Council through reception desk by ensuring visitors are registered and cleared
- Managing incoming and outgoing calls and routing them to the relevant office/personnel
- Registering inward and outgoing mail
- Attending to customer complaints, inquiries, concerns and queries and communicating to clients
- Providing relevant information to stakeholders as may be required''',
                'qualifications': [
                    'Certificate in Mass Communications, Customer Care, Public Relations',
                    'KCSE Grade D or equivalent',
                    'Computer proficiency'
                ],
                'category': operations,
                'department': 'Operations',
                'location': 'Nairobi',
                'county': 'Nairobi',
                'employment_type': 'full_time',
                'application_deadline': timezone.now() + timedelta(days=30),
                'status': 'published',
                'max_applications': 50,
                'auto_screening': True,
                'require_cover_letter': True,
                'posted_by': default_user,
            }
        ]

        created_count = 0
        for job_data in jobs_data:
            job, created = JobPost.objects.get_or_create(
                title=job_data['title'],
                defaults=job_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created job: {job.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample jobs')
        )
