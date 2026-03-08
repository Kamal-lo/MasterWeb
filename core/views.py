from django.contrib import messages
from django.shortcuts import render, redirect
from core.model import Students, DiplomesAnterieurs, Reclamation, Enrollments, Grades, DemandeRecorrection, Modules



def home(request):
    return render(request,'home.html')

  #methode  d authenfication
def login_view(request):
    
    if request.method == "POST":
        # On ajoute .strip() pour enlever les espaces accidentels au début ou à la fin
        cin_saisi = request.POST.get('cin', '').strip()
        cne_saisi = request.POST.get('massar_code', '').strip()

        try:
            # On cherche l'étudiant dans la base de données
            etudiant = Students.objects.get(cin=cin_saisi, massar_code=cne_saisi)
            
            # On crée une session pour "garder" l'étudiant connecté
            request.session['etudiant_id'] = etudiant.id_student
            request.session['nom_complet'] = f"{etudiant.first_name_fr} {etudiant.last_name_fr}"
            
            return redirect('dashboard')
            
        except Students.DoesNotExist:
            # Si le CIN ou le CNE est faux, on renvoie une erreur
            context = {
                'error': 'CIN ou Code Massar incorrect. Veuillez réessayer.',
                'cin_pre-rempli': cin_saisi # Optionnel : pour ne pas tout retaper
            }
            return render(request, 'login.html', context)

    return render(request, 'login.html')

def dashboard(request):
    return render(request,'dashboard.html')

def reponse_demande(request):
    student_id = request.session.get('etudiant_id')
    if not student_id:
        return redirect('login')
        
    try:
        etudiant = Students.objects.get(id_student=student_id)
        # On récupère toutes les demandes de cet étudiant
        demandes = DemandeRecorrection.objects.filter(student=etudiant).order_by('-date_demande').select_related('module')
        
        # On va créer une liste pour passer les données au template (incluant la note initiale si on veut l'afficher)
        demandes_data = []
        for d in demandes:
            # Essayer de trouver la note initiale via Enrollment et Grades
            enrollment = Enrollments.objects.filter(id_student=etudiant, module_code=d.module).first()
            note_initiale = None
            if enrollment:
                grade = Grades.objects.filter(id_enrollment=enrollment).first()
                if grade and grade.note_sn is not None:
                    note_initiale = grade.note_sn
            
            demandes_data.append({
                'date': d.date_demande,
                'module_code': d.module.module_code,
                'module_nom': d.module.module_name,
                'note_initiale': note_initiale,
                'nouvelle_note': d.nouvelle_note,
                'statut': d.statut,
                'commentaire': d.commentaire_admin,
            })
            
    except Students.DoesNotExist:
        return redirect('login')

    return render(request, 'reponse_demande.html', {
        'etudiant': etudiant,
        'demandes': demandes_data
    })

def demande_rec(request):
    student_id = request.session.get('etudiant_id')
    if not student_id:
        return redirect('login')
        
    try:
        etudiant = Students.objects.get(id_student=student_id)
        # On récupère les modules de l'étudiant via ses inscriptions
        enrollments = Enrollments.objects.filter(id_student=etudiant).select_related('module_code')
        modules_etu = []
        for e in enrollments:
            grade = Grades.objects.filter(id_enrollment=e).first()
            note = 0.0
            if grade and getattr(grade, 'note_sn', None) is not None:
                note = grade.note_sn

            modules_etu.append({
                'code': e.module_code.module_code if e.module_code else '',
                'nom': e.module_code.module_name if e.module_code else 'Module Inconnu',
                'note': note
            })
    except Students.DoesNotExist:
        return redirect('login')

    # Vérifier si l'étudiant a déjà soumis une demande de recorrection
    deja_soumis = DemandeRecorrection.objects.filter(student=etudiant).exists()

    if request.method == 'POST':
        if deja_soumis:
            messages.error(request, "Vous avez déjà soumis une demande de recorrection. Vous ne pouvez pas en soumettre une autre.")
            return redirect('demande')

        modules_selectionnes = request.POST.getlist('modules')
        remarque = request.POST.get('remarque', '').strip()

        if not modules_selectionnes:
            messages.warning(request, "Veuillez sélectionner au moins un module.")
        elif len(modules_selectionnes) > 2:
            messages.error(request, "Vous ne pouvez demander la recorrection que pour 2 modules maximum.")
        else:
            try:
                # Créer une demande pour chaque module sélectionné
                for module_code in modules_selectionnes:
                    module_obj = Modules.objects.get(module_code=module_code)
                    
                    # Vérifier si une demande n'existe pas déjà pour ce module
                    if not DemandeRecorrection.objects.filter(student=etudiant, module=module_obj).exists():
                        DemandeRecorrection.objects.create(
                            student=etudiant,
                            module=module_obj,
                            remarque=remarque
                        )
                messages.success(request, "Votre demande de recorrection a été envoyée avec succès.")
            except Modules.DoesNotExist:
                messages.error(request, "Un module sélectionné est invalide.")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")
                
        return redirect('demande')

    return render(request, 'demande_rec.html', {
        'etudiant': etudiant,
        'modules': modules_etu,
        'deja_soumis': deja_soumis
    })

def emplois_temps(request):
    return render(request,'emplois_du_temp.html')

def actuelle(request):
    return render(request,'actuelle.html')

def group(request):
    return render(request,'group.html')

def resultat(request):
    student_id = request.session.get('etudiant_id')
    if not student_id:
        return redirect('login')
        
    try:
        etudiant = Students.objects.get(id_student=student_id)
        enrollments = Enrollments.objects.filter(id_student=etudiant).select_related('module_code')
        
        notes = []
        for e in enrollments:
            grade = Grades.objects.filter(id_enrollment=e).first()
            if grade:
                sn = float(grade.note_sn) if grade.note_sn is not None else 0.0
                sr = float(grade.note_sr) if grade.note_sr is not None else None
                
                res_sn = 'V' if sn >= 10 else 'RAT'
                finale = sn
                if sr is not None and sr > sn:
                    finale = sr
                
                notes.append({
                    'module': e.module_code.module_name if e.module_code else 'Module Inconnu',
                    'sn': sn,
                    'res_sn': res_sn,
                    'sr': sr if sr is not None else '-',
                    'finale': finale
                })
                
    except Students.DoesNotExist:
        return redirect('login')
        
    return render(request, 'resultat.html', {'notes': notes, 'etudiant': etudiant})

def information_scolaire(request):
    # Récupération de l'ID de l'étudiant connecté
    student_id = request.session.get('etudiant_id')
    
    if not student_id:
        return redirect('login')

    try:
        etudiant = Students.objects.get(id_student=student_id)
        # Récupération des diplômes pour le tableau du bas
        diplomes = DiplomesAnterieurs.objects.filter(student=etudiant).order_by('annee')
    except Students.DoesNotExist:
        return redirect('login')

    return render(request, 'infoscol.html', {
        'etudiant': etudiant,
        'diplomes': diplomes
    })

def information_prive(request):
    student_id = request.session.get('etudiant_id')
    if not student_id:
        return redirect('login')
    
    try:
        etudiant = Students.objects.get(id_student=student_id)
    except Students.DoesNotExist:
        return redirect('login')

    # --- VERIFICATION SI UNE DEMANDE EXISTE DEJA ---
    deja_soumis = Reclamation.objects.filter(student=etudiant).exists()

    if request.method == 'POST':
        # Sécurité serveur : on ne traite pas si déjà soumis
        if deja_soumis:
            messages.error(request, "Vous avez déjà soumis une demande de rectification.")
            return redirect('information_prive')

        champs = request.POST.getlist('champ[]')
        valeurs = request.POST.getlist('valeur[]')
        fichier = request.FILES.get('justificatif')

        if champs and valeurs and fichier:
            # Vérification de la taille (5 Mo)
            if fichier.size > 5 * 1024 * 1024:
                messages.error(request, "Le fichier est trop lourd. Taille maximale : 5 Mo.")
                return redirect('information_prive')

            try:
                for i in range(len(champs)):
                    if champs[i].strip() != "" and valeurs[i].strip() != "":
                        Reclamation.objects.create(
                            student=etudiant,
                            champ_a_modifier=champs[i],
                            nouvelle_valeur=valeurs[i],
                            justificatif=fichier,
                            statut='En attente'
                        )
                messages.success(request, "Votre dossier de modification a été enregistré avec succès.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'insertion : {e}")
        else:
            messages.warning(request, "Veuillez remplir les champs et joindre un justificatif.")
        
        return redirect('information_prive')

    # Partie GET
    diplomes = DiplomesAnterieurs.objects.filter(student=etudiant).order_by('-annee')
    reclamations = Reclamation.objects.filter(student=etudiant).order_by('-date_demande')

    return render(request, 'infopers.html', {
        'etudiant': etudiant,
        'diplomes': diplomes,
        'reclamations': reclamations,
        'deja_soumis': deja_soumis, # On envoie l'info au HTML
    })