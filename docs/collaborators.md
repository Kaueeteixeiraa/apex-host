# Guia para colaboradores Apex Host

Este guia explica como Devs e Viewers acessam o Apex Host depois do Go Live.

## Acessar

Abra o link publico informado pelo Admin:

```text
https://host.{BASE_DOMAIN}
```

Use e-mail e senha cadastrados. Se a conta ainda estiver pendente, aguarde aprovacao de um Admin.

## Criar conta

1. Abra a tela de login.
2. Clique em `Cadastro`.
3. Informe nome, e-mail e senha forte.
4. Escolha tipo de conta:
   - `Dev`: cria e deploya projetos quando aprovado.
   - `Viewer`: visualiza projetos e logs.
   - `Admin`: apenas com codigo interno forte ou criacao pelo Admin.

Admins nao devem ser criados livremente por cadastro publico.

## Criar projeto

1. Acesse `Projetos`.
2. Clique em `Novo projeto`.
3. Escolha GitHub, template ou projeto interno Apex.
4. Revise repo, branch, comandos, porta, dominio e variaveis.
5. Clique em criar e acompanhe o deploy.

## Ver logs

- Abra `Logs` para logs gerais.
- Abra um projeto e use a aba `Logs` para logs filtrados.
- Em `Deploys`, abra o deploy e leia a etapa exata que falhou.

## Redeploy

1. Abra o projeto.
2. Clique em `Redeploy` ou acesse `Deploys`.
3. Confira etapas: clone, dependencias, build, container, Nginx, SSL, health check.

## Acessar link publicado

Use o dominio principal do card do projeto. Para Apex Realms, o padrao recomendado e:

```text
https://realms.{BASE_DOMAIN}
```

## Permissoes

- Admin: gerencia usuarios, projetos, settings, auditoria e infraestrutura.
- Dev: cria projetos, configura variaveis e executa deploys conforme limites.
- Viewer: visualiza projetos, logs e status sem alterar producao.
