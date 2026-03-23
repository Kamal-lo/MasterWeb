from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
import hashlib
from functools import wraps
from core.model import (
    Students, Filiere, Modules, Enrollments, Grades,
    Reclamation, DemandeRecorrection, Professor, AdminAccount, DiplomesAnterieurs
)

# ============================================================
# DÉCORATEUR D'AUTHENTIFICATION ADMIN
# ============================================================
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ============================================================
# CONNEXION / DÉCONNEXION ADMIN
# ============================================================
def admin_login(request):
    if request.method == 'POST':
        username_saisi = request.POST.get('username', '').strip()
        password_saisi = request.POST.get('password', '')
        hashed_password = hashlib.sha256(password_saisi.encode()).hexdigest()

        try:
            admin = AdminAccount.objects.get(username=username_saisi)
            if admin.password_hash == hashed_password:
                if admin.is_active:
                    request.session['admin_id'] = admin.id_account
                    request.session['admin_username'] = admin.username
                    request.session['admin_role'] = admin.role
                    return redirect('admin_dashboard')
                else:
                    return render(request, 'admin/admin_login.html', {'error': 'Ce compte est désactivé.'})
            else:
                return render(request, 'admin/admin_login.html', {'error': 'Mot de passe incorrect.'})
        except AdminAccount.DoesNotExist:
            return render(request, 'admin/admin_login.html', {'error': "Nom d'utilisateur introuvable."})

    return render(request, 'admin/admin_login.html')

def admin_logout(request):
    if 'admin_id' in request.session:
        del request.session['admin_id']
    if 'admin_username' in request.session:
        del request.session['admin_username']
    if 'admin_role' in request.session:
        del request.session['admin_role']
    return redirect('admin_login')


# ============================================================
# 1. DASHBOARD
# ============================================================
@admin_required
def admin_dashboard(request):
    context = {
        'active_page': 'dashboard',
        'total_students': Students.objects.count(),
        'total_professors': Professor.objects.count(),
        'total_filieres': Filiere.objects.count(),
        'total_modules': Modules.objects.count(),
        'total_reclamations': Reclamation.objects.filter(statut='En attente').count(),
        'total_recorrections': DemandeRecorrection.objects.filter(statut='En cours').count(),
        'recent_reclamations': Reclamation.objects.select_related('student').order_by('-date_demande')[:5],
        'recent_recorrections': DemandeRecorrection.objects.select_related('student', 'module').order_by('-date_demande')[:5],
    }
    return render(request, 'admin/dashboard.html', context)


# ============================================================
# 2. GESTION DES ÉTUDIANTS
# ============================================================
@admin_required
def admin_students(request):
    query = request.GET.get('q', '')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            Students.objects.create(
                first_name_fr=request.POST.get('first_name_fr', ''),
                last_name_fr=request.POST.get('last_name_fr', ''),
                first_name_ar=request.POST.get('first_name_ar', ''),
                last_name_ar=request.POST.get('last_name_ar', ''),
                cin=request.POST.get('cin', ''),
                massar_code=request.POST.get('massar_code', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                birth_date=request.POST.get('birth_date') or None,
                lieu_naissance=request.POST.get('lieu_naissance', ''),
            )
            messages.success(request, "Étudiant ajouté avec succès.")

        elif action == 'delete':
            student_id = request.POST.get('student_id')
            Students.objects.filter(id_student=student_id).delete()
            messages.success(request, "Étudiant supprimé.")

        return redirect('admin_students')

    students = Students.objects.all()
    if query:
        students = students.filter(
            Q(first_name_fr__icontains=query) |
            Q(last_name_fr__icontains=query) |
            Q(cin__icontains=query) |
            Q(massar_code__icontains=query)
        )

    return render(request, 'admin/students.html', {
        'active_page': 'students',
        'students': students,
        'query': query,
    })


# ============================================================
# 3. GESTION DES NOTES
# ============================================================
@admin_required
def admin_grades(request):
    filieres = Filiere.objects.all()
    modules = Modules.objects.all()
    selected_filiere = request.GET.get('filiere', '')
    selected_module = request.GET.get('module', '')
    query = request.GET.get('q', '')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'edit_grade':
            grade_id = request.POST.get('grade_id')
            grade = get_object_or_404(Grades, id_grade=grade_id)
            note_sn = request.POST.get('note_sn')
            note_sr = request.POST.get('note_sr')
            grade.note_sn = float(note_sn) if note_sn else None
            grade.note_sr = float(note_sr) if note_sr else None
            grade.save()
            messages.success(request, "Note modifiée avec succès.")
        return redirect('admin_grades')

    # Filtrer les modules par filière si sélectionnée
    if selected_filiere:
        modules = modules.filter(id_filiere_id=selected_filiere)

    # Construire les données des notes
    grades_data = []
    enrollments = Enrollments.objects.select_related('id_student', 'module_code').all()

    if selected_module:
        enrollments = enrollments.filter(module_code_id=selected_module)
    elif selected_filiere:
        enrollments = enrollments.filter(module_code__id_filiere_id=selected_filiere)

    if query:
        enrollments = enrollments.filter(
            Q(id_student__first_name_fr__icontains=query) |
            Q(id_student__last_name_fr__icontains=query) |
            Q(id_student__cin__icontains=query)
        )

    for e in enrollments[:100]:  # Limiter à 100 résultats
        grade = Grades.objects.filter(id_enrollment=e).first()
        if grade:
            grades_data.append({
                'grade_id': grade.id_grade,
                'student_name': f"{e.id_student.first_name_fr} {e.id_student.last_name_fr}" if e.id_student else "—",
                'module_code': e.module_code.module_code if e.module_code else "—",
                'module_name': e.module_code.module_name if e.module_code else "",
                'note_sn': grade.note_sn,
                'note_sr': grade.note_sr,
            })

    return render(request, 'admin/grades.html', {
        'active_page': 'grades',
        'filieres': filieres,
        'modules': modules,
        'grades_data': grades_data,
        'selected_filiere': selected_filiere,
        'selected_module': selected_module,
        'query': query,
    })


# ============================================================
# 4. GESTION FILIÈRES & MODULES
# ============================================================
@admin_required
def admin_modules(request):
    query = request.GET.get('q', '')

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- Filière CRUD ---
        if action == 'add_filiere':
            Filiere.objects.create(
                filiere_name=request.POST.get('filiere_name', ''),
                branch_short_name=request.POST.get('branch_short_name', ''),
            )
            messages.success(request, "Filière ajoutée.")

        elif action == 'edit_filiere':
            f = get_object_or_404(Filiere, id_filiere=request.POST.get('filiere_id'))
            f.filiere_name = request.POST.get('filiere_name', '')
            f.branch_short_name = request.POST.get('branch_short_name', '')
            f.save()
            messages.success(request, "Filière modifiée.")

        elif action == 'delete_filiere':
            Filiere.objects.filter(id_filiere=request.POST.get('filiere_id')).delete()
            messages.success(request, "Filière supprimée.")

        # --- Module CRUD ---
        elif action == 'add_module':
            filiere_id = request.POST.get('id_filiere') or None
            Modules.objects.create(
                module_code=request.POST.get('module_code', ''),
                module_name=request.POST.get('module_name', ''),
                semester=request.POST.get('semester') or None,
                coefficient=request.POST.get('coefficient') or None,
                id_filiere_id=filiere_id,
            )
            messages.success(request, "Module ajouté.")

        elif action == 'edit_module':
            old_code = request.POST.get('old_module_code')
            m = get_object_or_404(Modules, module_code=old_code)
            m.module_name = request.POST.get('module_name', '')
            m.semester = request.POST.get('semester') or None
            m.coefficient = request.POST.get('coefficient') or None
            filiere_id = request.POST.get('id_filiere') or None
            m.id_filiere_id = filiere_id
            m.save()
            messages.success(request, "Module modifié.")

        elif action == 'delete_module':
            Modules.objects.filter(module_code=request.POST.get('module_code')).delete()
            messages.success(request, "Module supprimé.")

        return redirect('admin_modules')

    filieres = Filiere.objects.annotate(module_count=Count('modules')).all()
    modules = Modules.objects.select_related('id_filiere').all()
    if query:
        modules = modules.filter(
            Q(module_code__icontains=query) | Q(module_name__icontains=query)
        )

    return render(request, 'admin/modules.html', {
        'active_page': 'modules',
        'filieres': filieres,
        'filieres_all': Filiere.objects.all(),
        'modules': modules,
        'query': query,
    })


# ============================================================
# 5. GESTION DES PROFESSEURS
# ============================================================
@admin_required
def admin_professors(request):
    query = request.GET.get('q', '')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            filiere_id = request.POST.get('filiere') or None
            Professor.objects.create(
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                specialite=request.POST.get('specialite', ''),
                filiere_id=filiere_id,
            )
            messages.success(request, "Professeur ajouté.")

        elif action == 'edit':
            p = get_object_or_404(Professor, id_professor=request.POST.get('professor_id'))
            p.first_name = request.POST.get('first_name', '')
            p.last_name = request.POST.get('last_name', '')
            p.email = request.POST.get('email', '')
            p.phone = request.POST.get('phone', '')
            p.specialite = request.POST.get('specialite', '')
            filiere_id = request.POST.get('filiere') or None
            p.filiere_id = filiere_id
            p.save()
            messages.success(request, "Professeur modifié.")

        elif action == 'delete':
            Professor.objects.filter(id_professor=request.POST.get('professor_id')).delete()
            messages.success(request, "Professeur supprimé.")

        return redirect('admin_professors')

    professors = Professor.objects.select_related('filiere').all()
    if query:
        professors = professors.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, 'admin/professors.html', {
        'active_page': 'professors',
        'professors': professors,
        'filieres': Filiere.objects.all(),
        'query': query,
    })


# ============================================================
# 6. GESTION DES COMPTES
# ============================================================
@admin_required
def admin_accounts(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            password = request.POST.get('password', '')
            hashed = hashlib.sha256(password.encode()).hexdigest()
            AdminAccount.objects.create(
                username=request.POST.get('username', ''),
                password_hash=hashed,
                role=request.POST.get('role', 'admin'),
            )
            messages.success(request, "Compte créé avec succès.")

        elif action == 'toggle':
            acc = get_object_or_404(AdminAccount, id_account=request.POST.get('account_id'))
            acc.is_active = not acc.is_active
            acc.save()
            messages.success(request, f"Compte {'activé' if acc.is_active else 'désactivé'}.")

        elif action == 'delete':
            AdminAccount.objects.filter(id_account=request.POST.get('account_id')).delete()
            messages.success(request, "Compte supprimé.")

        return redirect('admin_accounts')

    return render(request, 'admin/accounts.html', {
        'active_page': 'accounts',
        'accounts': AdminAccount.objects.all().order_by('-date_created'),
    })
