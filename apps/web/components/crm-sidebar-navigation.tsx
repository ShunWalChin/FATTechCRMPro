'use client';

import {useEffect, useState} from 'react';
import Link from 'next/link';
import {ChevronDown} from 'lucide-react';
import {SYNAPSE_NAVIGATION, navigationHref, navigationLocation} from './crm-navigation';
import styles from './crm-navigation.module.css';

const STORAGE_KEY = 'synapse.navigation.expanded.v3';

export function CrmNavigation({pathname, onNavigate}: {pathname: string; onNavigate: () => void}) {
  const current = navigationLocation(pathname);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY);
      if (value) {
        const parsed: unknown = JSON.parse(value);
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          setExpanded(Object.fromEntries(Object.entries(parsed).filter((entry): entry is [string, boolean] => typeof entry[1] === 'boolean')));
        }
      }
    } catch {
      // O menu segue utilizável se o navegador bloquear o armazenamento.
    }
  }, []);

  function toggle(id: string, initiallyOpen: boolean) {
    setExpanded(previous => {
      const next = {...previous, [id]: !(previous[id] ?? initiallyOpen)};
      try {window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));} catch {}
      return next;
    });
  }

  return <nav className={styles.navigation} aria-label="Navegação do SYNAPSE">
    {SYNAPSE_NAVIGATION.map(group => {
      // Página ativa abre por padrão; o usuário ainda pode recolher o grupo.
      const groupOpen = expanded[group.id] ?? (current?.group.id === group.id);
      const GroupIcon = group.icon;
      return <div key={group.id} className={styles.group}>
        <button type="button" className={`${styles.groupButton} ${current?.group.id === group.id ? styles.selected : ''}`}
          aria-expanded={groupOpen} aria-controls={`nav-group-${group.id}`} onClick={() => toggle(group.id, current?.group.id === group.id)}>
          <GroupIcon size={18} strokeWidth={1.8} aria-hidden="true"/>
          <span>{group.label}</span><ChevronDown size={16} className={groupOpen ? styles.chevronOpen : styles.chevron} aria-hidden="true"/>
        </button>
        <div id={`nav-group-${group.id}`} className={styles.groupContent} hidden={!groupOpen}>
          {group.sections.map(section => {
            const sectionKey = `${group.id}:${section.id}`;
            const sectionActive = current?.group.id === group.id && current.section.id === section.id;
            const sectionOpen = expanded[sectionKey] ?? sectionActive;
            return <div key={section.id} className={styles.section}>
              <button type="button" className={styles.sectionButton} aria-expanded={sectionOpen}
                aria-controls={`nav-section-${group.id}-${section.id}`} onClick={() => toggle(sectionKey, sectionActive)}>
                <span>{section.label}</span><ChevronDown size={14} className={sectionOpen ? styles.chevronOpen : styles.chevron} aria-hidden="true"/>
              </button>
              <div id={`nav-section-${group.id}-${section.id}`} className={styles.links} hidden={!sectionOpen}>
                {section.items.map(item => {
                  const href = navigationHref(item.route);
                  const active = current?.item.route === item.route;
                  const Icon = item.icon;
                  return <Link key={item.route} href={href} onClick={onNavigate} className={`${styles.link} ${active ? styles.active : ''}`}
                    aria-current={active ? 'page' : undefined}>
                    <Icon size={16} strokeWidth={1.7} aria-hidden="true"/><span>{item.label}</span>
                  </Link>;
                })}
              </div>
            </div>;
          })}
        </div>
      </div>;
    })}
  </nav>;
}
