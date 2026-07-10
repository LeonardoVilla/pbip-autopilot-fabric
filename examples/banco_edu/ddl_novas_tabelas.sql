USE banco_edu;
SET NAMES utf8mb4;

DROP TABLE IF EXISTS mensalidades;
DROP TABLE IF EXISTS matriz_curricular;
DROP TABLE IF EXISTS dim_calendario;

CREATE TABLE dim_calendario (
  data_id           INT         NOT NULL,
  data              DATE        NOT NULL,
  ano               INT         NOT NULL,
  mes               INT         NOT NULL,
  dia               INT         NOT NULL,
  trimestre         INT         NOT NULL,
  semestre          INT         NOT NULL,
  nome_mes          VARCHAR(15) NOT NULL,
  nome_mes_abrev    VARCHAR(5)  NOT NULL,
  nome_dia_semana   VARCHAR(15) NOT NULL,
  dia_semana        INT         NOT NULL,
  fim_de_semana     TINYINT     NOT NULL,
  ano_mes           VARCHAR(7)  NOT NULL,
  ano_semestre      VARCHAR(8)  NOT NULL,
  PRIMARY KEY (data_id),
  UNIQUE KEY uk_data (data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE matriz_curricular (
  matriz_id          BIGINT      NOT NULL AUTO_INCREMENT,
  curso_id           BIGINT      NOT NULL,
  disciplina_id      BIGINT      NOT NULL,
  semestre_sugerido  INT         NOT NULL,
  obrigatoria        TINYINT     NOT NULL DEFAULT 1,
  criado_em          TIMESTAMP   NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (matriz_id),
  UNIQUE KEY uk_curso_disc (curso_id, disciplina_id),
  KEY idx_mc_disc (disciplina_id),
  CONSTRAINT fk_mc_curso FOREIGN KEY (curso_id) REFERENCES cursos (curso_id),
  CONSTRAINT fk_mc_disc  FOREIGN KEY (disciplina_id) REFERENCES disciplinas (disciplina_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE mensalidades (
  mensalidade_id   BIGINT        NOT NULL AUTO_INCREMENT,
  aluno_id         BIGINT        NOT NULL,
  competencia      DATE          NOT NULL,
  valor            DECIMAL(10,2) NOT NULL,
  data_vencimento  DATE          NOT NULL,
  data_pagamento   DATE          DEFAULT NULL,
  valor_pago       DECIMAL(10,2) DEFAULT NULL,
  status           ENUM('pago','pendente','atrasado','isento') NOT NULL DEFAULT 'pendente',
  forma_pagamento  ENUM('boleto','cartao','pix','transferencia') DEFAULT NULL,
  criado_em        TIMESTAMP     NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (mensalidade_id),
  UNIQUE KEY uk_aluno_comp (aluno_id, competencia),
  KEY idx_mens_aluno (aluno_id),
  CONSTRAINT fk_mens_aluno FOREIGN KEY (aluno_id) REFERENCES alunos (aluno_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

SELECT 'DDL novas tabelas OK' AS resultado;
