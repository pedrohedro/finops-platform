'use client';

import React from 'react';
import {
  Server,
  ShieldCheck,
  Database,
  Activity,
  ChevronRight,
  MessageCircle,
  Cloud,
  CheckCircle2,
  Lock,
  Zap,
  RefreshCw,
  BarChart3,
  Terminal,
  ShieldAlert
} from 'lucide-react';

/**
 * 🤖 Applying knowledge of @[frontend-specialist] based on WebStation Brand Audit...
 *
 * Design Principles:
 * - Typography: Work Sans (Modern & Clean)
 * - Colors: ws-navy (#001529), ws-blue (#3079BD), ws-whatsapp (#25D366)
 * - Shapes: Pill-shaped buttons (24px radius), Rounded cards (32px)
 * - Layout: Clean, professional, intercalated sections (Zebra Pattern)
 */

export default function PMEProductPage() {
  return (
    <div className="bg-white font-work text-slate-900 selection:bg-ws-blue/20 w-full overflow-x-hidden">

      {/* Floating WhatsApp Action */}
      <a
        href="#contato-especialista"
        className="fixed bottom-8 right-8 z-50 bg-ws-whatsapp hover:brightness-110 text-white p-4 rounded-full shadow-lg transition-all hover:scale-110 active:scale-95 flex items-center justify-center group"
        aria-label="Contactar via WhatsApp"
      >
        <MessageCircle className="w-6 h-6" />
      </a>

      {/* Hero Section: WebStation Standard */}
      <section className="relative min-h-[85vh] flex items-center pt-20 pb-20 bg-ws-navy overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-ws-blue/10 blur-[150px] rounded-full -translate-y-1/2 translate-x-1/2"></div>

        <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-20">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-ws-blue/20 text-blue-300 border border-ws-blue/30 mb-8 font-bold text-xs uppercase tracking-widest">
              <Terminal className="w-4 h-4" /> Cloud MSP Excellence
            </div>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white leading-tight mb-8 tracking-tight">
              Sua empresa merece <br/>
              <span className="text-ws-blue">Paz Mental</span> na Nuvem.
            </h1>
            <p className="text-xl text-slate-300 mb-12 leading-relaxed max-w-[60ch]">
              Assuma o controle total da sua infraestrutura com a WebStation. Proteção contra ransomware, estabilidade garantida e custos previsíveis para o seu negócio.
            </p>
            <div className="flex flex-col sm:flex-row gap-6">
              <a href="#planos-pme" className="px-10 py-5 bg-ws-blue hover:bg-ws-blue/90 text-white rounded-full font-bold text-sm uppercase tracking-widest transition-all shadow-lg text-center">
                Explorar Pacotes
              </a>
              <a href="#contato-especialista" className="px-10 py-5 bg-white text-ws-navy hover:bg-slate-100 rounded-full font-bold text-sm uppercase tracking-widest transition-all shadow-md text-center">
                Consultoria Gratuita
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Productized Catalog: Standardized UI */}
      <section id="servicos-pme" className="py-32 bg-white relative">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="mb-24 text-center">
            <h2 className="text-xs font-bold text-ws-blue uppercase tracking-[0.4em] mb-4">Catálogo de Serviços</h2>
            <p className="text-3xl md:text-5xl font-bold text-ws-navy max-w-3xl mx-auto tracking-tight leading-tight">
              Soluções integradas com a experiência <br/> WebStation® em AWS.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <ServiceCard
              icon={<ShieldCheck className="w-8 h-8 text-ws-blue" />}
              title="Cloud Backup Essencial"
              desc="Blindagem total contra Ransomware. Dados encriptados com testes automáticos de restore e retenção inteligente."
            />
            <ServiceCard
              icon={<RefreshCw className="w-8 h-8 text-ws-blue" />}
              title="Cloud Continuidade"
              desc="DR Light para crises de missão crítica. Replicamos seus dados entre regiões para garantir que o seu negócio não pare."
            />
            <ServiceCard
              icon={<Server className="w-8 h-8 text-ws-blue" />}
              title="Cloud Infra Gerenciada"
              desc="Servidores AWS sempre atualizados e monitorados 24/7. Patching e performance geridos por especialistas."
            />
            <ServiceCard
              icon={<Database className="w-8 h-8 text-ws-blue" />}
              title="Cloud Banco Gerenciado"
              desc="Sua base de dados em alta disponibilidade. Performance Tuning e backups automáticos para workloads reais."
            />
            <ServiceCard
              icon={<Zap className="w-8 h-8 text-ws-blue" />}
              title="Cloud App Escalável"
              desc="Sua aplicação aguenta picos de acesso sem cair. Usamos ECS Fargate e Load Balancers para escalabilidade."
            />
            <ServiceCard
              icon={<BarChart3 className="w-8 h-8 text-ws-blue" />}
              title="Cloud Observabilidade"
              desc="Visibilidade total via OpenTelemetry. Alertas inteligentes antes mesmo do seu cliente perceber um problema."
            />
          </div>
        </div>
      </section>

      {/* Official Tiers: Predictable Maturity */}
      <section id="planos-pme" className="py-32 bg-slate-50 relative border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2 className="text-4xl font-bold text-ws-navy mb-6 tracking-tight">Níveis de Serviço</h2>
            <p className="text-slate-600 text-lg max-w-2xl mx-auto leading-relaxed">
              Tranquilidade operacional com modelos de preço fixo mensal, sem surpresas na fatura AWS.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-10 items-stretch">
            <TierCard
              name="IntegraBASIC"
              tier="STARTER"
              subtitle="O Essencial para PME"
              features={[
                "Cloud Backup Essencial",
                "Segurança Basica & MFA",
                "Monitoramento Comercial",
                "Alertas via E-mail",
                "Relatórios Mensais"
              ]}
              actionText="Assinar Essencial"
            />

            <TierCard
              name="IntegraPRO"
              tier="PRO"
              subtitle="Operação em Escala"
              highlight={true}
              features={[
                "Tudo do IntegraBASIC",
                "Infraestrutura Gerenciada",
                "Banco de Dados Gerenciado",
                "Alertas no Slack 24/7",
                "Restore Assistido"
              ]}
              actionText="Assinar Profissional"
            />

            <TierCard
              name="CustomField"
              tier="PREMIUM"
              subtitle="Missão Crítica"
              features={[
                "Tudo do IntegraPRO",
                "DR Cross-Region",
                "Alta Disponibilidade",
                "CI/CD WebStation",
                "SLA de Atendimento Formal"
              ]}
              actionText="Consultar Engenharia"
            />
          </div>
        </div>
      </section>

      {/* The WebStation Mission */}
      <section className="py-32 bg-ws-navy text-white text-center relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 relative z-10">
          <h2 className="text-xs font-bold text-ws-blue uppercase tracking-[0.5em] mb-12">Nossa Missão</h2>
          <blockquote className="text-3xl md:text-4xl font-medium leading-snug mb-12">
            "Simplificar a complexidade da nuvem para que você possa focar no crescimento real do seu negócio."
          </blockquote>
          <div className="flex justify-center gap-12 text-blue-200/50">
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white">20+</span>
              <span className="text-xs uppercase tracking-widest mt-2">Anos de História</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white">100%</span>
              <span className="text-xs uppercase tracking-widest mt-2">Comprometimento</span>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Form: WebStation Style */}
      <section id="contato-especialista" className="py-32 bg-white">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 grid lg:grid-cols-2 gap-20 items-center">
          <div>
            <h2 className="text-4xl font-bold text-ws-navy mb-8 tracking-tight">Fale com um Especialista</h2>
            <p className="text-slate-600 text-lg mb-12 leading-relaxed">
              Inicie sua jornada para uma nuvem profissional e segura. Nossos arquitetos estão prontos para diagnosticar sua infraestrutura atual.
            </p>
            <div className="space-y-6">
              <div className="flex items-center gap-4 text-ws-navy font-bold">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
                  <CheckCircle2 className="text-ws-blue" />
                </div>
                <span>Diagnostico Gratuito</span>
              </div>
              <div className="flex items-center gap-4 text-ws-navy font-bold">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
                  <CheckCircle2 className="text-ws-blue" />
                </div>
                <span>Proposta Personalizada</span>
              </div>
            </div>
          </div>

          <form className="bg-slate-50 p-10 rounded-[2rem] border border-slate-200 shadow-sm space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <FormField label="Nome" placeholder="Seu nome" />
              <FormField label="E-mail" type="email" placeholder="nome@empresa.com" />
            </div>
            <FormField label="Empresa" placeholder="Sua empresa" />
            <div>
              <label className="block text-slate-500 font-bold mb-3 text-[10px] uppercase tracking-widest">Serviço de Interesse</label>
              <select className="w-full h-[58px] px-6 rounded-2xl bg-white border border-slate-200 text-ws-navy focus:outline-none focus:ring-2 focus:ring-ws-blue/20 appearance-none">
                <option value="starter">IntegraBASIC (Starter)</option>
                <option value="pro">IntegraPRO (Profissional)</option>
                <option value="premium">CustomField (Premium)</option>
              </select>
            </div>
            <button className="w-full bg-ws-blue hover:brightness-110 text-white font-bold uppercase tracking-widest py-5 rounded-full transition-all shadow-md">
              Enviar Solicitação
            </button>
          </form>
        </div>
      </section>

      <footer className="py-20 bg-ws-navy text-slate-500 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="text-white font-bold text-xl italic">WebStation<span className="text-ws-blue">.</span></div>
          <p className="text-sm">© 2026 WebStation. Todos os direitos reservados.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition-colors">Atendimento</a>
            <a href="#" className="hover:text-white transition-colors">Termos</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function ServiceCard({ icon, title, desc }: { icon: any, title: string, desc: string }) {
  return (
    <div className="p-10 rounded-[2rem] bg-slate-50 border border-slate-200 hover:border-ws-blue/50 transition-all group">
      <div className="mb-8 p-5 bg-white rounded-3xl shadow-sm w-fit group-hover:scale-110 transition-transform duration-500">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-ws-navy mb-4 tracking-tight">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function TierCard({ name, tier, subtitle, features, actionText, highlight = false }: any) {
  return (
    <div className={`relative flex flex-col p-12 rounded-[2.5rem] border transition-all duration-500 ${
      highlight
      ? 'bg-ws-navy text-white border-ws-navy shadow-2xl scale-105 z-10'
      : 'bg-white text-ws-navy border-slate-200 hover:shadow-xl'
    }`}>
      {highlight && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-6 py-1.5 bg-ws-blue text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-full shadow-lg">
          Mais Recomendado
        </div>
      )}
      <div className="mb-12">
        <span className={`text-[10px] font-black tracking-widest uppercase block mb-3 ${highlight ? 'text-ws-blue' : 'text-slate-400'}`}>
          {tier}
        </span>
        <h3 className="text-3xl font-bold mb-2">{name}</h3>
        <p className={`text-sm ${highlight ? 'text-slate-400' : 'text-slate-500'}`}>{subtitle}</p>
      </div>

      <ul className="space-y-6 mb-12 flex-grow">
        {features.map((f: any, i: any) => (
          <li key={i} className="flex items-center gap-4">
            <CheckCircle2 className={`w-5 h-5 shrink-0 ${highlight ? 'text-ws-blue' : 'text-ws-blue'}`} />
            <span className="text-sm font-medium">{f}</span>
          </li>
        ))}
      </ul>

      <button className={`w-full py-5 rounded-full font-bold uppercase text-[11px] tracking-widest transition-all ${
        highlight
        ? 'bg-ws-blue text-white hover:brightness-110'
        : 'bg-ws-navy text-white hover:bg-ws-navy/90'
      }`}>
        {actionText}
      </button>
    </div>
  );
}

function FormField({ label, type = "text", placeholder }) {
  return (
    <div className="flex flex-col gap-3">
      <label className="text-slate-500 font-bold text-[10px] uppercase tracking-widest">{label}</label>
      <input
        type={type}
        placeholder={placeholder}
        className="h-[58px] px-6 rounded-2xl bg-white border border-slate-200 text-ws-navy placeholder-slate-300 focus:outline-none focus:ring-2 focus:ring-ws-blue/20 transition-all font-medium"
      />
    </div>
  );
}
