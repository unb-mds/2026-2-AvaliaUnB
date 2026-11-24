// Banco descartável: node tests/validar_anonimato_sql.mjs <caminho-do-pglite/dist/index.js>
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const {PGlite}=await import(pathToFileURL(process.argv[2]).href);
const db=new PGlite();
const autor='00000000-0000-0000-0000-000000000001';
const outro='00000000-0000-0000-0000-000000000002';
try {
  await db.exec(`
    CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;
    CREATE SCHEMA auth;
    CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS
      $$ SELECT nullif(current_setting('teste.usuario',true),'')::uuid $$;
    GRANT USAGE ON SCHEMA auth TO anon,authenticated;
    CREATE TABLE perfis(id uuid PRIMARY KEY,username text);
    CREATE TABLE professores(id bigint PRIMARY KEY);
    CREATE TABLE disciplinas(id bigint PRIMARY KEY);
    CREATE TABLE turmas(professor_id bigint,disciplina_id bigint);
    INSERT INTO perfis VALUES('${autor}','identidade_autor'),('${outro}','identidade_outro');
    INSERT INTO professores VALUES(1); INSERT INTO disciplinas VALUES(10);
    INSERT INTO turmas VALUES(1,10);
    GRANT SELECT ON perfis,turmas TO anon,authenticated;
  `);
  await db.exec(await readFile(new URL('../docs/migrations/002_comentarios.sql',import.meta.url),'utf8'));
  await db.exec(`
    GRANT ALL ON comentarios TO service_role;
    GRANT USAGE ON SEQUENCE comentarios_id_seq TO authenticated,service_role;
    INSERT INTO comentarios(usuario_id,professor_id,disciplina_id,texto) VALUES
      ('${autor}',1,10,'Texto existente'),('${outro}',1,10,'Outro texto');
    INSERT INTO comentarios(usuario_id,professor_id,disciplina_id,texto,ocultado_em)
      VALUES('${autor}',1,10,'Oculto',now());
  `);
  const migracao=await readFile(new URL('../docs/migrations/20261122155752_anonimato_comentarios.sql',import.meta.url),'utf8');
  await db.exec(migracao); await db.exec(migracao);
  const deny=sql=>assert.rejects(()=>db.query(sql),error=>error.code==='42501');
  for(const papel of ['anon','authenticated']) {
    await db.exec(`SET ROLE ${papel}; RESET teste.usuario;`);
    assert.deepEqual((await db.query('SELECT id,texto FROM comentarios ORDER BY id')).rows,
                     [{id:1,texto:'Texto existente'},{id:2,texto:'Outro texto'}]);
    await deny('SELECT usuario_id FROM comentarios');
    await deny('SELECT ocultado_em FROM comentarios');
    await deny('SELECT * FROM comentarios');
    await deny(`SELECT id FROM comentarios WHERE usuario_id='${autor}'`);
    await deny('SELECT p.username FROM comentarios c JOIN perfis p ON p.id=c.usuario_id');
    await db.exec('RESET ROLE');
  }
  await db.exec(`SET ROLE authenticated; SET teste.usuario='${autor}';`);
  assert.equal((await db.query('SELECT id FROM comentarios ORDER BY id')).rows.length,3,'Dono ainda vê o próprio ocultado, sem identidade.');
  await db.query("UPDATE comentarios SET texto='Atualizado pelo autor' WHERE id=1");
  assert.equal((await db.query('SELECT texto FROM comentarios WHERE id=1')).rows[0].texto,'Atualizado pelo autor');
  assert.equal((await db.query("UPDATE comentarios SET texto='Indevido' WHERE id=2 RETURNING id")).rows.length,0);
  await assert.rejects(()=>db.query(`INSERT INTO comentarios(usuario_id,professor_id,disciplina_id,texto) VALUES('${outro}',1,10,'Autor forjado')`));
  await db.query(`INSERT INTO comentarios(usuario_id,professor_id,disciplina_id,texto) VALUES('${autor}',1,10,'Novo comentário')`);
  assert.equal((await db.query('DELETE FROM comentarios WHERE id=2 RETURNING id')).rows.length,0);
  assert.equal((await db.query('DELETE FROM comentarios WHERE id=1 RETURNING id')).rows.length,1);
  await db.exec('RESET ROLE; SET ROLE service_role;');
  assert.equal((await db.query('SELECT usuario_id FROM comentarios WHERE id=2')).rows[0].usuario_id,outro);
  await db.query("UPDATE comentarios SET texto='Revisado no backend' WHERE id=2");
  assert.equal((await db.query('SELECT texto FROM comentarios WHERE id=2')).rows[0].texto,'Revisado no backend');
  await db.exec('RESET ROLE;');
  const rls=(await db.query("SELECT relrowsecurity FROM pg_class WHERE oid='public.comentarios'::regclass")).rows[0];
  assert.equal(rls.relrowsecurity,true);
  console.log('SQL aprovado: leitura pública sem autoria, bloqueio de filtro/junção por autor, escrita própria, backend e RLS preservados.');
} finally { await db.close(); }
