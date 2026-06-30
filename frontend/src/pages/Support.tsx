import { FormEvent, useEffect, useState } from "react";
import { LifeBuoy, MessageSquare, Send } from "lucide-react";

import { FeedbackBanner } from "../components/FeedbackBanner";
import { PageHeader } from "../components/PageHeader";
import { api, formatDate, SupportTicket } from "../lib/api";

const initialForm = { subject: "", body: "", category: "deploy", priority: "medium" };

export function Support() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [form, setForm] = useState(initialForm);
  const [reply, setReply] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const selected = tickets.find((ticket) => ticket.id === selectedId) || tickets[0];

  const load = async () => {
    const data = await api<SupportTicket[]>("/support/tickets");
    setTickets(data);
    if (!selectedId && data[0]) setSelectedId(data[0].id);
  };

  useEffect(() => {
    void load();
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const ticket = await api<SupportTicket>("/support/tickets", { method: "POST", body: JSON.stringify(form) });
    setForm(initialForm);
    setSelectedId(ticket.id);
    setMessage("Ticket aberto com sucesso.");
    await load();
  };

  const sendReply = async () => {
    if (!selected || !reply.trim()) return;
    await api(`/support/tickets/${selected.id}/messages`, { method: "POST", body: JSON.stringify({ body: reply }) });
    setReply("");
    await load();
  };

  const resolve = async () => {
    if (!selected) return;
    await api<SupportTicket>(`/support/tickets/${selected.id}`, { method: "PATCH", body: JSON.stringify({ status: "resolved" }) });
    await load();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Help Desk"
        title="Central de suporte"
        description="Tickets por categoria, prioridade, historico de mensagens e respostas do admin."
        icon={LifeBuoy}
      />
      {message ? <FeedbackBanner type="success" message={message} /> : null}

      <section className="grid gap-4 lg:grid-cols-[380px_1fr]">
        <form className="panel space-y-4 p-4" onSubmit={submit}>
          <h2 className="font-semibold text-white">Abrir ticket</h2>
          <label>
            <span className="label">Assunto</span>
            <input className="field" value={form.subject} onChange={(event) => setForm({ ...form, subject: event.target.value })} required />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label>
              <span className="label">Categoria</span>
              <select className="field" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
                <option value="deploy">deploy</option>
                <option value="domain">dominio</option>
                <option value="account">conta</option>
                <option value="billing">cobranca</option>
                <option value="bug">bug</option>
                <option value="other">outro</option>
              </select>
            </label>
            <label>
              <span className="label">Prioridade</span>
              <select className="field" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>
                <option value="low">baixa</option>
                <option value="medium">media</option>
                <option value="high">alta</option>
              </select>
            </label>
          </div>
          <label>
            <span className="label">Mensagem</span>
            <textarea className="field min-h-32" value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} required />
          </label>
          <button className="btn-primary w-full">
            <Send className="h-4 w-4" />
            Enviar ticket
          </button>
        </form>

        <div className="grid gap-4 xl:grid-cols-[300px_1fr]">
          <div className="panel p-3">
            <h2 className="mb-3 px-1 font-semibold text-white">Tickets</h2>
            <div className="space-y-2">
              {tickets.map((ticket) => (
                <button
                  key={ticket.id}
                  className={`w-full rounded-md border p-3 text-left transition ${
                    selected?.id === ticket.id ? "border-apex-cyan bg-apex-cyan/10" : "border-apex-line bg-black/20 hover:border-apex-cyan/50"
                  }`}
                  onClick={() => setSelectedId(ticket.id)}
                >
                  <div className="text-sm font-medium text-white">{ticket.subject}</div>
                  <div className="mt-1 text-xs text-apex-muted">{ticket.status} - {ticket.priority}</div>
                </button>
              ))}
              {tickets.length === 0 ? <p className="muted p-2">Nenhum ticket aberto.</p> : null}
            </div>
          </div>

          <div className="panel flex min-h-[520px] flex-col p-4">
            {selected ? (
              <>
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{selected.subject}</h2>
                    <p className="muted">{selected.category} - {selected.priority} - {selected.status}</p>
                  </div>
                  <button className="btn-secondary" onClick={() => void resolve()}>Resolver</button>
                </div>
                <div className="flex-1 space-y-3 overflow-auto">
                  {selected.messages.map((item) => (
                    <div key={item.id} className={`rounded-md border p-3 ${item.is_admin_reply ? "border-apex-cyan/40 bg-apex-cyan/10" : "border-apex-line bg-black/20"}`}>
                      <div className="mb-1 flex items-center gap-2 text-xs text-apex-muted">
                        <MessageSquare className="h-3.5 w-3.5" />
                        {item.is_admin_reply ? "Admin" : "Usuario"} - {formatDate(item.created_at)}
                      </div>
                      <div className="whitespace-pre-wrap text-sm text-apex-text">{item.body}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <input className="field" value={reply} onChange={(event) => setReply(event.target.value)} placeholder="Responder ticket..." />
                  <button className="btn-primary" onClick={() => void sendReply()}>
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="grid flex-1 place-items-center text-apex-muted">Selecione ou abra um ticket.</div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
