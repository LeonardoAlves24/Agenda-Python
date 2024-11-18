create database bd_projetoPY;
use bd_projetoPY;

create table anotacoes(
	id int not null auto_increment primary key,
    nome_anotacao varchar(50) not null,
    descricao_anotacao varchar(200) null,
    data_anotacao date
);

create table usuarios (
	id_usuario integer not null auto_increment primary key,
    nome    varchar(32) not null,
    email    varchar(32) not null,
    senha	   varchar(32) not null,
    dtcria	   datetime default now(),
    estatus	   char(01) default ''
);

insert into anotacoes(nome_anotacao, descricao_anotacao, data_anotacao)
values				 ("Pagar faculdade", "retirar dinheiro da caixinha do nubank pra pagar", "2024-09-10");

select * from anotacoes;





