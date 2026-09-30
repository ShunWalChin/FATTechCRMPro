import Link from 'next/link';
import {ArrowUpRight} from 'lucide-react';
import {SYNAPSE_NAVIGATION, navigationHref} from '@/components/crm-navigation';
import styles from './platform.module.css';

export const metadata = {title: 'Início'};

export default function PlatformHome() {
  return <>
    <header className="crm-page-header">
      <div><span className="eyebrow">SYNAPSE · PLATAFORMA DE GESTÃO E INTELIGÊNCIA</span>
        <h1>Sua empresa, conectada.</h1>
        <p>Vendas, operação, comunicação e inteligência em um só lugar. Escolha onde trabalhar.</p>
      </div>
    </header>
    <nav className={styles.shortcuts} aria-label="Meu trabalho">
      <Link href="/crm/tarefas">Tarefas <ArrowUpRight size={16}/></Link>
      <Link href="/crm/aprovacoes">Aprovações <ArrowUpRight size={16}/></Link>
      <Link href="/crm/conversas">Conversas <ArrowUpRight size={16}/></Link>
    </nav>
    <section className={styles.modules} aria-label="Módulos do SYNAPSE">
      {SYNAPSE_NAVIGATION.filter(group => group.id !== 'inicio').map(group => {
        const Icon = group.icon;
        return <article className={styles.module} key={group.id}>
          <Icon size={24} aria-hidden="true"/>
          <h2>{group.label}</h2><p>{group.description}</p>
          <ul>{group.sections.map(section => <li key={section.id}>
            <Link href={navigationHref(section.items[0].route)}>{section.label}<ArrowUpRight size={15}/></Link>
          </li>)}</ul>
        </article>;
      })}
    </section>
    <p className={styles.note}>A disponibilidade de ações depende das suas permissões e das integrações configuradas. Confira a prontidão em <Link href="/crm/synapse">Implantação comercial</Link>.</p>
  </>;
}
