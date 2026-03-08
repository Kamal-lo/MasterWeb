# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Filiere(models.Model):
    id_filiere = models.BigAutoField(primary_key=True)
    filiere_name = models.CharField(max_length=100)
    branch_short_name = models.CharField(unique=True, max_length=10)

    class Meta:
        managed = True # On passe à True pour que Django puisse gérer la table
        db_table = 'filiere'
    
    def __str__(self):
        return self.branch_short_name

class Students(models.Model):
    id_student = models.BigAutoField(primary_key=True)
    massar_code = models.CharField(unique=True, max_length=20, blank=True, null=True)
    cin = models.CharField(unique=True, max_length=15, blank=True, null=True)
    last_name_fr = models.CharField(max_length=50, blank=True, null=True)
    last_name_ar = models.CharField(max_length=50, blank=True, null=True)
    first_name_fr = models.CharField(max_length=50, blank=True, null=True)
    first_name_ar = models.CharField(max_length=50, blank=True, null=True)
    
    birth_date = models.DateField(blank=True, null=True)
    lieu_naissance = models.CharField(max_length=100,null=True, blank=True)
    commune_naissance = models.CharField(max_length=30,null=True, blank=True)
    pays_naissance = models.CharField(max_length=30,null=True, blank=True)
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    province_bac = models.CharField(max_length=100, blank=True, null=True)
    annee_bac = models.IntegerField(blank=True, null=True)
    type_bac = models.CharField(max_length=100, blank=True, null=True)
    MENTIONS = [
    ('Passable', 'Passable'),
    ('Assez Bien', 'Assez Bien'),
    ('Bien', 'Bien'),
    ('Très Bien', 'Très Bien'),]
    mention_bac = models.CharField(max_length=15, choices=MENTIONS, default='Bien')
    
    class Meta:
        managed = True
        db_table = 'students'

    def __str__(self):
        return f"{self.first_name_fr} {self.last_name_fr}"

class Modules(models.Model):
    module_code = models.CharField(primary_key=True, max_length=20)
    module_name = models.CharField(max_length=100)
    semester = models.IntegerField(blank=True, null=True) # Corrigé de JSONField vers Integer
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    # Remplacement de l'entier par une vraie relation vers Filiere
    id_filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, db_column='id_filiere', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'modules'

class Enrollments(models.Model):
    id_enrollment = models.BigAutoField(primary_key=True)
    # On lie l'inscription à l'étudiant et au module
    id_student = models.ForeignKey(Students, on_delete=models.CASCADE, db_column='id_student', blank=True, null=True)
    module_code = models.ForeignKey(Modules, on_delete=models.CASCADE, db_column='module_code', blank=True, null=True)
    academic_year = models.CharField(max_length=10)
    ni = models.IntegerField(blank=True, null=True)
    section = models.CharField(max_length=5, blank=True, null=True)
    group_td = models.CharField(max_length=10, blank=True, null=True)
    group_tp = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'enrollments'

class Grades(models.Model):
    id_grade = models.BigAutoField(primary_key=True)
    # On lie la note directement à l'inscription
    id_enrollment = models.ForeignKey(Enrollments, on_delete=models.CASCADE, db_column='id_enrollment', blank=True, null=True)
    note_sn = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    note_sr = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'grades'

class DiplomesAnterieurs(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='diplomes')
    nom_diplome = models.CharField(max_length=50) # Ex: DEUG, Licence
    annee = models.IntegerField()
    filiere = models.CharField(max_length=100)
    moyenne = models.DecimalField(max_digits=4, decimal_places=2)
    mention = models.CharField(max_length=20)

    class Meta:
        db_table = 'diplomes_anterieurs'
        
class Reclamation(models.Model):
    CHAMPS_POSSIBLES = [
        ('first_name_fr', 'Prénom (Français)'),
        ('last_name_fr', 'Nom (Français)'),
        ('first_name_ar', 'Prénom (Arabe)'),
        ('last_name_ar', 'Nom (Arabe)'),
        ('date_naissance', 'Date de Naissance'),
        ('lieu_naissance', 'Lieu de Naissance'),
        ('telephone', 'Numéro de Téléphone'),
        ('cin', 'narte d identite national'),
        ('massar_code', 'code_massar'),
        ('email', 'Adresse Email Personnel'), # L'étudiant peut maintenant modifier son email officiel
    ]

    STATUT_CHOICES = [
        ('En attente', 'En attente'),
        ('Validé', 'Validé'),
        ('Rejeté', 'Rejeté'),
    ]

    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    
    # Email de suivi (où l'admin enverra la réponse à cette demande)
    email_suivi = models.EmailField(max_length=255, verbose_name="Email pour le suivi")
    
    champ_a_modifier = models.CharField(max_length=50, choices=CHAMPS_POSSIBLES)
    ancienne_valeur = models.CharField(max_length=255, blank=True)
    nouvelle_valeur = models.CharField(max_length=255)
    
    justificatif = models.FileField(upload_to='reclamations/preuves/')
    
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='En attente')

    def __str__(self):
        return f"Réclamation de {self.student.last_name_fr} - {self.champ_a_modifier}"
    


    # Relation avec l'étudiant (on force le nom de colonne SQL student_id)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, db_column='student_id')
    
    # Champ pour la rectification
    champ_a_modifier = models.CharField(max_length=50, choices=CHAMPS_POSSIBLES)
    nouvelle_valeur = models.CharField(max_length=255)
    justificatif = models.FileField(upload_to='reclamations/preuves/')
    
    # Métadonnées
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='En attente')

    class Meta:
        managed = True
        db_table = 'reclamation' # Nom exact de votre table SQL

    def __str__(self):
        return f"{self.student.last_name_fr} - {self.champ_a_modifier}"

class DemandeRecorrection(models.Model):
    STATUT_CHOICES = [
        ('En cours', 'En cours'),
        ('Traitée', 'Traitée'),
        ('Rejetée', 'Rejetée'),
    ]

    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    module = models.ForeignKey(Modules, on_delete=models.CASCADE)
    remarque = models.TextField(blank=True, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='En cours')
    nouvelle_note = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    commentaire_admin = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'demande_recorrection'

    def __str__(self):
        return f"Recorrection {self.module.module_code} - {self.student.last_name_fr}"
