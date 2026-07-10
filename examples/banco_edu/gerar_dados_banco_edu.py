# -*- coding: utf-8 -*-
"""
Gerador de dados de exemplo coerentes para o banco_edu (MariaDB / XAMPP).
- Escala "realista": dimensoes crescem moderadamente, fatos ganham volume,
  espalhados por 7 semestres (2023/1 .. 2026/1).
- Preenche as tabelas vazias e adiciona 3 tabelas novas:
  dim_calendario, matriz_curricular, mensalidades.
- Reproduzivel (random.seed). Guarda contra dupla execucao. Transacao unica.
"""
import random
from datetime import date, timedelta
import pymysql

random.seed(42)
HOJE = date(2026, 7, 9)

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="",
                       database="banco_edu", charset="utf8mb4", autocommit=False)
cur = conn.cursor()

# ---------- Guarda contra dupla execucao ----------
cur.execute("SELECT COUNT(*) FROM alunos")
if cur.fetchone()[0] > 10:
    print("ABORTADO: o banco ja parece escalado (alunos > 10). Nada foi feito.")
    conn.close(); raise SystemExit(0)

def ins(sql, params):
    cur.execute(sql, params)
    return cur.lastrowid

# ============================================================
# 1. DEPARTAMENTOS (add 2 -> total 6)
# ============================================================
dept_ids = {1:1,2:2,3:3,4:4}  # existentes (Exatas, Humanas, Eng, Saude)
for nome, sigla in [("Tecnologia da Informacao","TI"), ("Artes e Design","ARTES")]:
    did = ins("INSERT INTO departamentos (nome,sigla,ativo) VALUES (%s,%s,1)", (nome,sigla))
    if sigla=="TI": dept_ids[5]=did
    else: dept_ids[6]=did
DEP_EXATAS,DEP_HUM,DEP_ENG,DEP_SAU,DEP_TI,DEP_ART = 1,2,3,4,dept_ids[5],dept_ids[6]

# ============================================================
# 2. PROFESSORES (add ~17 -> total 22)
# ============================================================
PRIMEIROS = ["Ana","Carlos","Beatriz","Eduardo","Fernanda","Gabriel","Helena","Igor",
    "Juliana","Marcos","Patricia","Ricardo","Sofia","Thiago","Vanessa","Bruno","Camila",
    "Daniel","Larissa","Rodrigo","Mariana","Felipe","Aline","Gustavo","Renata","Leandro",
    "Priscila","Otavio","Tatiane","Wesley"]
SOBRENOMES = ["Souza","Silva","Lima","Ramos","Costa","Oliveira","Santos","Pereira","Almeida",
    "Nunes","Carvalho","Rocha","Gomes","Martins","Barbosa","Ribeiro","Araujo","Fernandes",
    "Cardoso","Teixeira","Moraes","Freitas","Correia","Pinto","Moreira"]
TITULACOES = ["graduacao","especializacao","mestrado","doutorado","pos_doutorado"]

def nome_aleatorio(usados):
    while True:
        n = f"{random.choice(PRIMEIROS)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        if n not in usados:
            usados.add(n); return n

prof_por_dept = {DEP_EXATAS:[1,2], DEP_HUM:[3], DEP_ENG:[4], DEP_SAU:[5],
                 DEP_TI:[], DEP_ART:[]}
nomes_usados=set(["Ana Paula Souza","Carlos Silva","Beatriz Lima","Eduardo Ramos","Fernanda Costa"])
emails_prof=set()
# distribuicao alvo de professores adicionais por depto
add_profs = {DEP_EXATAS:3, DEP_HUM:3, DEP_ENG:3, DEP_SAU:2, DEP_TI:4, DEP_ART:2}
for dep, qtd in add_profs.items():
    for _ in range(qtd):
        nome = nome_aleatorio(nomes_usados)
        base = nome.lower().replace(" ",".")
        for ch in "aeiouc": base=base
        base = (nome.split()[0]+"."+nome.split()[-1]).lower()
        base = (base.replace("á","a").replace("ã","a").replace("â","a").replace("é","e")
                    .replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o")
                    .replace("õ","o").replace("ú","u").replace("ç","c"))
        email=f"{base}@exemplo.edu"; k=1
        while email in emails_prof:
            k+=1; email=f"{base}{k}@exemplo.edu"
        emails_prof.add(email)
        adm = date(random.randint(2008,2022), random.randint(1,12), random.randint(1,28))
        tit = random.choice(TITULACOES)
        pid = ins("""INSERT INTO professores (departamento_id,nome,email,titulacao,data_admissao,ativo)
                     VALUES (%s,%s,%s,%s,%s,1)""",(dep,nome,email,tit,adm))
        prof_por_dept[dep].append(pid)

# ============================================================
# 3. DISCIPLINAS (add -> total ~30)
# ============================================================
disc_por_dept = {DEP_EXATAS:[1,2,3], DEP_HUM:[4], DEP_ENG:[5], DEP_SAU:[6], DEP_TI:[], DEP_ART:[]}
disc_info = {}  # disc_id -> (creditos, carga)
for d in [1,2,3]: disc_info[d]=(4,60)
disc_info[4]=(4,60); disc_info[5]=(2,30); disc_info[6]=(4,60)
NOVAS_DISC = [
 (DEP_EXATAS,"MAT201","Calculo II",4,60), (DEP_EXATAS,"MAT202","Estatistica",4,60),
 (DEP_EXATAS,"MAT203","Geometria Analitica",4,60), (DEP_EXATAS,"FIS102","Fisica II",4,60),
 (DEP_HUM,"HIS102","Historia Moderna",4,60), (DEP_HUM,"FIL101","Filosofia",4,60),
 (DEP_HUM,"SOC101","Sociologia",4,60), (DEP_HUM,"LET101","Lingua Portuguesa",4,60),
 (DEP_ENG,"ENG102","Mecanica dos Solidos",4,60), (DEP_ENG,"ENG103","Resistencia dos Materiais",4,60),
 (DEP_ENG,"ENG104","Hidraulica",4,60), (DEP_ENG,"ENG105","Topografia",3,45),
 (DEP_SAU,"SAU102","Fisiologia",4,60), (DEP_SAU,"SAU103","Farmacologia",4,60),
 (DEP_SAU,"SAU104","Enfermagem Clinica",4,60),
 (DEP_TI,"TI101","Algoritmos",4,60), (DEP_TI,"TI102","Estrutura de Dados",4,60),
 (DEP_TI,"TI103","Banco de Dados",4,60), (DEP_TI,"TI104","Redes de Computadores",4,60),
 (DEP_TI,"TI105","Engenharia de Software",4,60), (DEP_TI,"TI106","Programacao Web",4,60),
 (DEP_ART,"ART101","Desenho",3,45), (DEP_ART,"ART102","Historia da Arte",3,45),
 (DEP_ART,"ART103","Design Grafico",4,60),
]
for dep,cod,nome,cr,ch in NOVAS_DISC:
    did = ins("""INSERT INTO disciplinas (departamento_id,codigo,nome,creditos,carga_horaria,ementa,ativo)
                 VALUES (%s,%s,%s,%s,%s,%s,1)""",(dep,cod,nome,cr,ch,f"Ementa de {nome}."))
    disc_por_dept[dep].append(did); disc_info[did]=(cr,ch)

# ============================================================
# 4. CURSOS (add -> total ~19)
# ============================================================
curso_dep = {1:DEP_EXATAS,2:DEP_EXATAS,3:DEP_HUM,4:DEP_ENG,5:DEP_SAU}
curso_nivel = {1:"graduacao",2:"graduacao",3:"graduacao",4:"graduacao",5:"graduacao"}
NOVOS_CURSOS = [
 (DEP_EXATAS,"Estatistica","graduacao",3200,8), (DEP_EXATAS,"Licenciatura em Matematica","graduacao",3200,8),
 (DEP_HUM,"Filosofia","graduacao",3000,6), (DEP_HUM,"Letras","graduacao",3200,8),
 (DEP_ENG,"Engenharia Mecanica","graduacao",4000,10), (DEP_ENG,"Engenharia Eletrica","graduacao",4000,10),
 (DEP_SAU,"Fisioterapia","graduacao",4000,10), (DEP_SAU,"Tecnico em Enfermagem","tecnico",1800,4),
 (DEP_TI,"Ciencia da Computacao","graduacao",3600,8), (DEP_TI,"Analise e Desenvolvimento de Sistemas","tecnico",2400,5),
 (DEP_TI,"Tecnico em Informatica","tecnico",1600,3), (DEP_TI,"Pos em Ciencia de Dados","pos",600,3),
 (DEP_ART,"Design","graduacao",3200,8), (DEP_ART,"Tecnico em Design Grafico","tecnico",1600,3),
]
for dep,nome,nivel,cht,dur in NOVOS_CURSOS:
    cid = ins("""INSERT INTO cursos (departamento_id,nome,nivel,carga_horaria_total,duracao_semestres,ativo)
                 VALUES (%s,%s,%s,%s,%s,1)""",(dep,nome,nivel,cht,dur))
    curso_dep[cid]=dep; curso_nivel[cid]=nivel

# ============================================================
# 5. MATRIZ_CURRICULAR (nova) - disciplinas de cada curso por semestre
# ============================================================
mc_rows=[]
for cid, dep in curso_dep.items():
    discs = disc_por_dept.get(dep, [])[:]
    random.shuffle(discs)
    discs = discs[:min(6,len(discs))]
    for i, d in enumerate(discs):
        mc_rows.append((cid, d, (i%6)+1, 1 if random.random()<0.85 else 0))
cur.executemany("""INSERT INTO matriz_curricular (curso_id,disciplina_id,semestre_sugerido,obrigatoria)
                   VALUES (%s,%s,%s,%s)""", mc_rows)

# ============================================================
# 6. BLOCOS / SALAS / LABORATORIOS / EQUIPAMENTOS
# ============================================================
bloco_ids=[1,2]                       # existentes
bloco_letra={1:"A",2:"B"}
for nome,loc,lt in [("Bloco C","Predio Norte","C"),("Bloco D","Predio Sul","D")]:
    bid=ins("INSERT INTO blocos (nome,localizacao) VALUES (%s,%s)",(nome,loc))
    bloco_ids.append(bid); bloco_letra[bid]=lt
TIPOS_SALA=["teorica","laboratorio","auditorio","multiuso"]
sala_ids=[1,2,3,4]                     # existentes
codigos_sala=set(["A101","A102","B201","B202"])
sala_seq=0
for b in bloco_ids:
    for _ in range(3):                 # +3 salas por bloco
        sala_seq+=1
        cod=f"{bloco_letra[b]}3{sala_seq:02d}"
        while cod in codigos_sala: sala_seq+=1; cod=f"{bloco_letra[b]}3{sala_seq:02d}"
        codigos_sala.add(cod)
        tipo=random.choice(TIPOS_SALA)
        cap=random.choice([25,30,40,45,50,60])
        sid=ins("""INSERT INTO salas (bloco_id,codigo,capacidade,tipo,recursos,ativa)
                   VALUES (%s,%s,%s,%s,%s,1)""",(b,cod,cap,tipo,"Projetor, quadro"))
        sala_ids.append(sid)

# laboratorios: precisa de sala_id UNICO. sala 2 ja usada (lab 1). Usar 5 salas novas.
CATS=["quimica","fisica","robotica","maker","informatica"]
lab_ids=[1]
salas_livres=[s for s in sala_ids if s!=2][:] ; random.shuffle(salas_livres)
for i in range(5):
    sid=salas_livres[i]
    lid=ins("""INSERT INTO laboratorios (sala_id,categoria,quantidade_maquinas,software_instalado,normas_uso)
               VALUES (%s,%s,%s,%s,%s)""",(sid,CATS[i%len(CATS)],random.choice([0,10,15,20,25]),
               "Software padrao","Uso mediante agendamento"))
    lab_ids.append(lid)
# equipamentos (add ~22)
EQUIP=["Microscopio","Osciloscopio","Kit Robotica","Impressora 3D","Notebook","Projetor",
       "Balanca de Precisao","Multimetro","Estacao de Solda","Bancada Hidraulica"]
pat_seq=3
eq_rows=[]
for lid in lab_ids:
    for _ in range(random.randint(3,5)):
        eq_rows.append((lid, f"LAB{pat_seq:03d}", random.choice(EQUIP),
                        random.choice(["ativo","ativo","ativo","manutencao","baixado"])))
        pat_seq+=1
cur.executemany("""INSERT INTO equipamentos_laboratorio (laboratorio_id,patrimonio,descricao,status)
                   VALUES (%s,%s,%s,%s)""", eq_rows)

# ============================================================
# 7. TURMAS + TURMAS_DISCIPLINAS via COORTES
# ============================================================
SEMS=[(2023,1),(2023,2),(2024,1),(2024,2),(2025,1),(2025,2),(2026,1)]
def sem_dates(a,s):
    return (date(a,2,10),date(a,6,30)) if s==1 else (date(a,8,5),date(a,12,15))
def sem_idx(a,s): return SEMS.index((a,s))
TURNOS=["manha","tarde","noite","integral"]

# coortes: (curso_id, indice do semestre de ingresso, turno, n_alunos)
# usa cursos por nome
curso_por_nome={}
cur.execute("SELECT curso_id,nome FROM cursos")
for cid,nm in cur.fetchall(): curso_por_nome[nm]=cid
COORTES=[
 ("Matemática",0,"manha",10), ("Física",0,"tarde",9),
 ("Ciencia da Computacao",1,"noite",11), ("Engenharia Civil",2,"manha",10),
 ("Enfermagem",2,"integral",9), ("História",3,"noite",8),
 ("Design",4,"tarde",8), ("Analise e Desenvolvimento de Sistemas",4,"noite",10),
]
turmas=[]        # (turma_id, curso_id, ano, sem, turno, status)
td_list=[]       # (td_id, turma_id, disc_id, prof_id, status, sala_id, ano, sem)
codigos_turma=set(["MAT2023A","FIS2023A"])
SIGLA={"Matemática":"MAT","Física":"FIS","Ciencia da Computacao":"CC","Engenharia Civil":"ECIV",
       "Enfermagem":"ENF","História":"HIS","Design":"DES","Analise e Desenvolvimento de Sistemas":"ADS"}

# turmas/tds ja existentes (2023/1)
turmas.append((1,1,2023,1,"manha","concluida"))
turmas.append((2,2,2023,1,"tarde","concluida"))
td_list.append((1,1,1,1,"concluida",1,2023,1))
td_list.append((2,1,2,2,"concluida",1,2023,1))
td_list.append((3,2,3,1,"concluida",3,2023,1))
# marcar turmas/tds antigas como concluidas (estavam ativas/planejadas)
cur.execute("UPDATE turmas SET status='concluida' WHERE turma_id IN (1,2)")
cur.execute("UPDATE turmas_disciplinas SET status='concluida' WHERE turma_disciplina_id IN (1,2,3)")

cohort_turmas={}  # idx coorte -> lista de (td_id,...) por semestre
for ci,(cnome,ing,turno,nal) in enumerate(COORTES):
    cid=curso_por_nome[cnome]; dep=curso_dep[cid]
    discs=disc_por_dept[dep][:]; random.shuffle(discs)
    n_sem=min(6, len(SEMS)-ing)
    cohort_turmas[ci]=[]
    for k in range(n_sem):
        ano,sem=SEMS[ing+k]
        status_t = "ativa" if (ano,sem)==(2026,1) else "concluida"
        cod=f"{SIGLA[cnome]}{ano}{sem}{turno[0].upper()}"
        while cod in codigos_turma: cod+="X"
        codigos_turma.add(cod)
        tid=ins("""INSERT INTO turmas (curso_id,codigo,semestre_letivo,ano_letivo,turno,status)
                   VALUES (%s,%s,%s,%s,%s,%s)""",(cid,cod,str(sem),ano,turno,status_t))
        turmas.append((tid,cid,ano,sem,turno,status_t))
        # disciplinas do semestre k: 4 disciplinas (rotacionando o catalogo do dept)
        sem_discs=[discs[(k*4+j)%len(discs)] for j in range(4)]
        sem_discs=list(dict.fromkeys(sem_discs))  # remove dup mantendo ordem
        sala_fixa=random.choice(sala_ids)
        tds_deste=[]
        for d in sem_discs:
            prof=random.choice(prof_por_dept[dep]) if prof_por_dept[dep] else random.choice([1,2,3,4,5])
            st_td="em_andamento" if status_t=="ativa" else "concluida"
            cr,ch=disc_info[d]
            try:
                tdid=ins("""INSERT INTO turmas_disciplinas
                    (turma_id,disciplina_id,professor_id,periodo,carga_horaria_planejada,status)
                    VALUES (%s,%s,%s,'semestral',%s,%s)""",(tid,d,prof,ch,st_td))
            except pymysql.err.IntegrityError:
                continue
            td_list.append((tdid,tid,d,prof,st_td,sala_fixa,ano,sem))
            tds_deste.append((tdid,sala_fixa,ano,sem,st_td))
        cohort_turmas[ci].append((tid,ano,sem,status_t,tds_deste))

# ============================================================
# 8. ALUNOS (add ~75 -> total ~80) atrelados a coortes
# ============================================================
alunos=[]  # (aluno_id, cohort_idx)
matriculas_usadas=set(["20230001","20230002","20230003","20230004","20230005"])
emails_al=set()
mat_seq=1000
# existentes 1..5 pertencem a coorte 0 (Matematica) e 1 (Fisica)
existentes_coorte={1:0,2:0,3:0,4:1,5:1}
for aid,ci in existentes_coorte.items():
    alunos.append((aid,ci))

for ci,(cnome,ing,turno,nal) in enumerate(COORTES):
    ja = sum(1 for _,c in alunos if c==ci)
    for _ in range(max(0, nal-ja)):
        nome=nome_aleatorio(nomes_usados)
        ano_ing=SEMS[ing][0]
        mat=f"{ano_ing}{mat_seq}"; mat_seq+=1
        while mat in matriculas_usadas: mat=f"{ano_ing}{mat_seq}"; mat_seq+=1
        matriculas_usadas.add(mat)
        base=(nome.split()[0]+"."+nome.split()[-1]).lower()
        base=(base.replace("á","a").replace("ã","a").replace("â","a").replace("é","e")
                  .replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o")
                  .replace("õ","o").replace("ú","u").replace("ç","c"))
        email=f"{base}@aluno.exemplo.edu"; k=1
        while email in emails_al: k+=1; email=f"{base}{k}@aluno.exemplo.edu"
        emails_al.add(email)
        nasc=date(ano_ing-random.randint(17,26), random.randint(1,12), random.randint(1,28))
        ingr=sem_dates(*SEMS[ing])[0]
        st=random.choices(["ativo","trancado","evadido","concluido"],[0.78,0.08,0.06,0.08])[0]
        # turma_principal = turma da coorte no ultimo semestre
        tp=cohort_turmas[ci][-1][0]
        aid=ins("""INSERT INTO alunos (turma_principal_id,matricula,nome,email,data_nascimento,data_ingresso,status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",(tp,mat,nome,email,nasc,ingr,st))
        alunos.append((aid,ci))

# ============================================================
# 9. MATRICULAS + AULAS + FREQUENCIAS + AVALIACOES + NOTAS + RESUMO
# ============================================================
alunos_por_coorte={}
for aid,ci in alunos: alunos_por_coorte.setdefault(ci,[]).append(aid)

TURNO_HORARIO={"manha":("08:00:00","10:00:00"),"tarde":("14:00:00","16:00:00"),
               "noite":("19:00:00","21:00:00"),"integral":("10:00:00","12:00:00")}
mat_faltas={}  # matricula_id -> faltas
resumo_rows=[]
freq_rows=[]
nota_rows=[]
mens_rows=[]
aptidao={}  # aluno_id -> media base

for ci, turmas_da_coorte in cohort_turmas.items():
    for aid in alunos_por_coorte.get(ci,[]):
        apt=aptidao.setdefault(aid, max(2.0,min(9.8,random.gauss(6.6,1.6))))
        freq_rate=min(0.99,max(0.55,random.gauss(0.88,0.08)))
        for (tid,ano,sem,status_t,tds) in turmas_da_coorte:
            turno=[t[4] for t in [] ]
            # turno da turma:
            turno_t=[x for x in TURNOS]  # placeholder
            # recuperar turno real
            cur.execute("SELECT turno FROM turmas WHERE turma_id=%s",(tid,))
            turno_real=cur.fetchone()[0]
            hi,hf=TURNO_HORARIO[turno_real]
            ini,fim=sem_dates(ano,sem)
            for (tdid,sala,a2,s2,st_td) in tds:
                # matricula
                if status_t=="ativa":
                    m_status="cursando"
                else:
                    m_status=random.choices(["aprovado","reprovado","trancado","cancelado"],
                                            [0.80,0.12,0.05,0.03])[0]
                data_mat=ini - timedelta(days=random.randint(3,20))
                try:
                    mid=ins("""INSERT INTO matriculas (aluno_id,turma_disciplina_id,data_matricula,status,faltas)
                               VALUES (%s,%s,%s,%s,0)""",(aid,tdid,data_mat,m_status))
                except pymysql.err.IntegrityError:
                    continue
                mat_faltas[mid]=0
                # aulas desta TD (gera uma vez por TD; para nao duplicar, gera quando 1o aluno)
                # -> geramos aulas por TD num passo separado abaixo; aqui so matricula
        # (aulas/freq/notas geradas depois, por TD)

# --- AULAS por TD (uma vez cada) ---
aulas_por_td={}
for (tdid,tid,d,prof,st_td,sala,ano,sem) in td_list:
    cur.execute("SELECT turno FROM turmas WHERE turma_id=%s",(tid,))
    turno_real=cur.fetchone()[0]
    hi,hf=TURNO_HORARIO[turno_real]
    ini,fim=sem_dates(ano,sem)
    n_aulas=random.randint(10,14)
    ll=[]
    for i in range(n_aulas):
        d_aula=ini+timedelta(days=7*i)
        if d_aula>fim: break
        if st_td=="em_andamento":
            realizada = d_aula <= HOJE
            status_aula="realizada" if realizada else "planejada"
        else:
            status_aula="realizada"
        aula_id=ins("""INSERT INTO aulas (turma_disciplina_id,sala_id,data_aula,horario_inicio,horario_fim,
                        conteudo_planejado,conteudo_realizado,status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (tdid,sala,d_aula,hi,hf,f"Aula {i+1}",
                     f"Aula {i+1} ministrada" if status_aula=="realizada" else None,status_aula))
        ll.append((aula_id,status_aula))
    aulas_por_td[tdid]=ll

# --- AVALIACOES por TD (uma vez cada) ---
aval_por_td={}
TIPO_AVAL=[("prova","Prova 1",4.0),("prova","Prova 2",4.0),("trabalho","Trabalho",2.0)]
for (tdid,tid,d,prof,st_td,sala,ano,sem) in td_list:
    ini,fim=sem_dates(ano,sem)
    ll=[]
    for j,(tipo,titulo,peso) in enumerate(TIPO_AVAL):
        d_prev=ini+timedelta(days=30*(j+1))
        if st_td=="em_andamento":
            aplicada = d_prev<=HOJE
            status_av="aplicada" if aplicada else "planejada"
            d_apl=d_prev if aplicada else None
        else:
            status_av="fechada"; d_apl=d_prev
        av_id=ins("""INSERT INTO avaliacoes (turma_disciplina_id,tipo,titulo,peso,nota_maxima,
                     data_prevista,data_aplicacao,status) VALUES (%s,%s,%s,%s,10.00,%s,%s,%s)""",
                  (tdid,tipo,titulo,peso,d_prev,d_apl,status_av))
        ll.append((av_id,peso,status_av))
    aval_por_td[tdid]=ll

# --- FREQUENCIAS, NOTAS, RESUMO, FALTAS ---
# recarrega matriculas geradas
cur.execute("""SELECT m.matricula_id, m.aluno_id, m.turma_disciplina_id, m.status
               FROM matriculas m WHERE m.matricula_id>5""")
mats=cur.fetchall()
for (mid,aid,tdid,mstatus) in mats:
    apt=aptidao.get(aid, 6.5)
    freq_rate=min(0.99,max(0.55,random.gauss(0.88,0.08)))
    faltas=0
    for (aula_id,status_aula) in aulas_por_td.get(tdid,[]):
        if status_aula!="realizada": continue
        presente=1 if random.random()<freq_rate else 0
        if presente==0: faltas+=1
        freq_rows.append((aula_id,mid,presente,None))
    mat_faltas[mid]=faltas
    # notas
    soma_pw=0.0; soma_p=0.0; n_notas=0
    for (av_id,peso,status_av) in aval_por_td.get(tdid,[]):
        if status_av not in ("aplicada","fechada"): continue
        nota=round(min(10.0,max(0.0, random.gauss(apt,1.2))),2)
        nota_rows.append((av_id,mid,nota,None))
        soma_pw+=nota*float(peso); soma_p+=float(peso); n_notas+=1
    # resumo apenas para matriculas de turmas concluidas
    if mstatus in ("aprovado","reprovado") and n_notas>0:
        media=round(soma_pw/soma_p,2) if soma_p>0 else 0
        if media>=6: sf="aprovado"
        elif media>=4: sf="recuperacao"
        else: sf="reprovado"
        resumo_rows.append((mid,media,n_notas,sf))

if freq_rows:
    cur.executemany("""INSERT INTO frequencias (aula_id,matricula_id,presente,observacao)
                       VALUES (%s,%s,%s,%s)""",freq_rows)
if nota_rows:
    cur.executemany("""INSERT INTO notas (avaliacao_id,matricula_id,nota,observacao)
                       VALUES (%s,%s,%s,%s)""",nota_rows)
if resumo_rows:
    cur.executemany("""INSERT INTO resumo_matriculas (matricula_id,media_ponderada,total_avaliacoes,status_final)
                       VALUES (%s,%s,%s,%s)""",resumo_rows)
# atualiza faltas
for mid,f in mat_faltas.items():
    if f>0: cur.execute("UPDATE matriculas SET faltas=%s WHERE matricula_id=%s",(f,mid))

# ============================================================
# 10. PREREQUISITOS_DISCIPLINAS (~15)
# ============================================================
prereq=[(disc_por_dept[DEP_EXATAS][3],1),  # Calculo II <- Calculo I
        ]
prq=[]
# regra simples: dentro de cada dept, disciplina[i] tem prereq disciplina[i-1]
for dep,ds in disc_por_dept.items():
    for i in range(1,len(ds)):
        if random.random()<0.5:
            prq.append((ds[i],ds[i-1]))
prq=list({(a,b) for a,b in prq if a!=b})
if prq:
    cur.executemany("""INSERT IGNORE INTO prerequisitos_disciplinas (disciplina_id,prerequisito_disciplina_id)
                       VALUES (%s,%s)""",prq)

# ============================================================
# 11. MENSALIDADES (nova) - por aluno x mes de vinculo
# ============================================================
FORMAS=["boleto","cartao","pix","transferencia"]
cur.execute("SELECT aluno_id,data_ingresso FROM alunos")
alunos_all=cur.fetchall()
# nivel do curso do aluno via turma_principal->curso
def valor_por_aluno(aid):
    cur.execute("""SELECT c.nivel FROM alunos a
                   JOIN turmas t ON t.turma_id=a.turma_principal_id
                   JOIN cursos c ON c.curso_id=t.curso_id WHERE a.aluno_id=%s""",(aid,))
    r=cur.fetchone(); niv=r[0] if r else "graduacao"
    return {"tecnico":480.00,"graduacao":890.00,"pos":1250.00}.get(niv,890.00)

for aid,ingresso in alunos_all:
    if ingresso is None: continue
    valor=valor_por_aluno(aid)
    # gera competencias mensais de ingresso ate min(hoje+2meses, +30 meses)
    y,m=ingresso.year,ingresso.month
    for _ in range(30):
        comp=date(y,m,1)
        if comp>date(2026,9,1): break
        venc=date(y,m,10)
        if venc>HOJE:
            status="pendente"; dpag=None; vpag=None; forma=None
        else:
            r=random.random()
            if r<0.82:
                status="pago"; dpag=venc+timedelta(days=random.randint(-3,4))
                vpag=valor; forma=random.choice(FORMAS)
            elif r<0.92:
                status="atrasado";
                if random.random()<0.5:
                    dpag=venc+timedelta(days=random.randint(6,40)); vpag=valor; forma=random.choice(FORMAS)
                else:
                    dpag=None; vpag=None; forma=None
            elif r<0.97:
                status="pendente"; dpag=None; vpag=None; forma=None
            else:
                status="isento"; dpag=None; vpag=None; forma=None
        mens_rows.append((aid,comp,valor,venc,dpag,vpag,status,forma))
        m+=1
        if m>12: m=1; y+=1
cur.executemany("""INSERT INTO mensalidades
   (aluno_id,competencia,valor,data_vencimento,data_pagamento,valor_pago,status,forma_pagamento)
   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",mens_rows)

# ============================================================
# 12. DIM_CALENDARIO (nova) - 2023..2026
# ============================================================
MESES=["Janeiro","Fevereiro","Marco","Abril","Maio","Junho","Julho","Agosto",
       "Setembro","Outubro","Novembro","Dezembro"]
MESES_AB=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
DIAS=["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"]
cal_rows=[]
d=date(2023,1,1); fim=date(2026,12,31)
while d<=fim:
    dow=d.weekday()  # 0=segunda
    cal_rows.append((int(d.strftime("%Y%m%d")), d, d.year, d.month, d.day,
                     (d.month-1)//3+1, 1 if d.month<=6 else 2,
                     MESES[d.month-1], MESES_AB[d.month-1], DIAS[dow], dow+1,
                     1 if dow>=5 else 0, d.strftime("%Y-%m"),
                     f"{d.year}-S{1 if d.month<=6 else 2}"))
    d+=timedelta(days=1)
cur.executemany("""INSERT INTO dim_calendario
  (data_id,data,ano,mes,dia,trimestre,semestre,nome_mes,nome_mes_abrev,
   nome_dia_semana,dia_semana,fim_de_semana,ano_mes,ano_semestre)
   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",cal_rows)

conn.commit()
print("OK: dados gerados e commitados.")
conn.close()
