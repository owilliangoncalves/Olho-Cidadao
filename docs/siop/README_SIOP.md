# SIOP SPARQL

Documentação para explorar o endpoint SPARQL do **SIOP (Sistema Integrado de Planejamento e Orçamento)**.

O que encontramos aqui:

- exploração do dataset RDF do orçamento federal
- engenharia reversa do modelo de dados

**Endpoint utilizado:**  
<http://www1.siop.planejamento.gov.br/sparql/>

---

## 1) O que é o SIOP

O **SIOP** é o sistema do Governo Federal responsável pelo **planejamento e orçamento público**.

Os dados disponibilizados no endpoint SPARQL estão organizados em **RDF (Linked Data)**, ou seja, em **grafos**.

Isso significa que as informações são representadas como triplas:

```text

sujeito → predicado → objeto

```

Exemplo conceitual:

```text

ItemDespesa → temFuncao → Saúde

```

---

## 2) Como os dados são armazenados

Cada **ano do orçamento** é armazenado em um **grafo separado**.

Formato:

```text

[http://orcamento.dados.gov.br/{ano}/](http://orcamento.dados.gov.br/{ano}/)

```

Exemplo:

```text

[http://orcamento.dados.gov.br/2024/](http://orcamento.dados.gov.br/2024/)

```

Isso permite consultar diretamente um exercício específico.

---

## 3) Nome aos bois

Ao utilizarmos:

```text

[http://vocab.e.gov.br/2013/09/loa#](http://vocab.e.gov.br/2013/09/loa#)

```

os parâmetros:

```text

/2013/09

```

referem-se à **data de publicação do vocabulário RDF** usado para descrever o orçamento.

Ou seja, **não é o ano do orçamento**, mas sim a versão da utilizada.

Esse vocabulário define propriedades como:

```text

ItemDespesa
temFuncao
temPrograma
valorPago
valorEmpenhado

```

Outro vocabulário utilizado é:

```text

[http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#)

```

Esse é o padrão **RDF Schema**, publicado pelo **W3C**, que fornece propriedades como:

```text

rdfs:label

```

usada para obter o **nome legível de um recurso**.

---

## 4) Pulando no rio

## Funções do governo

A propriedade:

```text

temFuncao

````

define a **função orçamentária**, ou seja, a área de atuação do governo.

Exemplos:

- Saúde
- Educação
- Segurança Pública

Para descobrir todas as funções disponíveis, podemos executar:

```sparql
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?funcao ?nome
WHERE {
  GRAPH <http://orcamento.dados.gov.br/2024/> {

    ?item a loa:ItemDespesa .
    ?item loa:temFuncao ?funcao .
    ?funcao rdfs:label ?nome .
  }
}
ORDER BY ?funcao
````

No crawler do projeto, o filtro por função é feito pelo código no último
segmento de `?funcao`, e não por uma URI montada manualmente. Isso foi
substituído por uma consulta leve de IDs paginada por cursor, usando
`?funcao loa:codigo "<codigo>"` e `FILTER(STR(?item) > "<ultima_uri>")`,
no mesmo estilo dos scripts oficiais do SIOP. Assim, o crawler evita o custo
de `OFFSET` alto em Virtuoso.

Depois disso, o enriquecimento dos itens é feito em lotes pequenos com
`FILTER(?item IN (...))`, evitando `VALUES ?item`, que o endpoint rejeita.

Resultado observado no momento da criação do script:

| Código da Função | Descrição da Função     |
| ---------------- | ----------------------- |
| 01               | Legislativa             |
| 02               | Judiciário              |
| 03               | Essencial à Justiça     |
| 04               | Administração           |
| 05               | Defesa Nacional         |
| 06               | Segurança Pública       |
| 07               | Relações Exteriores     |
| 08               | Assistência Social      |
| 09               | Previdência Social      |
| 10               | Saúde                   |
| 11               | Trabalho                |
| 12               | Educação                |
| 13               | Cultura                 |
| 14               | Direitos da Cidadania   |
| 15               | Urbanismo               |
| 16               | Habitação               |
| 17               | Saneamento              |
| 18               | Gestão Ambiental        |
| 19               | Ciência e Tecnologia    |
| 20               | Agricultura             |
| 21               | Organização Agrária     |
| 22               | Indústria               |
| 23               | Comércio e Serviços     |
| 24               | Comunicação             |
| 25               | Energia                 |
| 26               | Transporte              |
| 27               | Desporto e Lazer        |
| 28               | Encargos Especiais      |
| 99               | Reserva de Contingência |

---

## 5) Descobrindo os grafos disponíveis

Para listar todos os grafos presentes no endpoint:

```sparql
SELECT DISTINCT ?g
WHERE {
  GRAPH ?g {
    ?s ?p ?o
  }
}
```

Entre os grafos encontrados estão:

- grafos do orçamento (`orcamento.dados.gov.br`)
- grafos de vocabulário
- grafos do sistema Virtuoso

Os grafos relevantes para análise são os que seguem o padrão:

```text
orcamento.dados.gov.br/{ano}
```

---

## 6) Pipeline de execução

A primeira execução do projeto segue a lógica:

```text
Consulta todos os grafos
↓
Identifica o menor e o maior ano disponível
↓
Consulta todas as funções por ano (para verificar mudanças)
↓
Consulta o orçamento por função em todos os anos
↓
Retorna a série histórica
```

Para **execuções futuras**, o pipeline pode ser simplificado:

```text
Consultar apenas o orçamento do ano atual
```

---

## 7) Dicionário de dados

O dicionário oficial do SIOP está disponível em:

[https://www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos](https://www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos)
