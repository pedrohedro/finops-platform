"use client"

import { useEffect, useRef, useState } from "react"
import { Bot, Loader2, SendHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"

type ChatMessage = { role: "user" | "assistant"; content: string }

const MAX_INPUT_CHARS = 4000
// The API accepts at most 20 alternating turns, starting with the user.
const MAX_HISTORY_TURNS = 19

const SUGGESTIONS = [
  "Quanto gastamos nos últimos 30 dias e como isso se compara ao período anterior?",
  "Quais os 5 serviços mais caros este mês?",
  "Qual time mais gastou nos últimos 7 dias?",
]

const ERROR_MESSAGES: Record<number, string> = {
  429: "O agente está ocupado ou atingiu o limite diário. Tente novamente em instantes.",
  503: "O agente não está disponível agora.",
}

function trimHistory(messages: ChatMessage[]): ChatMessage[] {
  let trimmed = messages.slice(-MAX_HISTORY_TURNS)
  while (trimmed.length > 0 && trimmed[0].role !== "user") {
    trimmed = trimmed.slice(1)
  }
  return trimmed
}

export function AgentChat({ apiUrl }: { apiUrl: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  async function send(text: string) {
    const content = text.trim()
    if (!content || loading) return

    const history = trimHistory([...messages, { role: "user", content }])
    setMessages(history)
    setInput("")
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${apiUrl}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      })
      if (!res.ok) {
        throw new Error(ERROR_MESSAGES[res.status] ?? "Não foi possível obter uma resposta.")
      }
      const data: { reply?: unknown } = await res.json()
      const reply = typeof data.reply === "string" ? data.reply : ""
      setMessages([...history, { role: "assistant", content: reply || "(resposta vazia)" }])
    } catch (e) {
      // Drop the unanswered turn so the history keeps alternating.
      setMessages(history.slice(0, -1))
      setInput(content)
      setError(e instanceof Error ? e.message : "Erro inesperado.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          className="fixed bottom-6 right-6 z-50 h-12 rounded-full px-5 shadow-lg"
          aria-label="Abrir o Agente FinOps"
        >
          <Bot className="w-5 h-5 mr-2" />
          Agente FinOps
        </Button>
      </SheetTrigger>

      <SheetContent className="flex w-full flex-col gap-0 p-0 sm:max-w-md">
        <SheetHeader className="border-b border-border p-4">
          <SheetTitle>Agente FinOps</SheetTitle>
          <SheetDescription>
            Pergunte sobre os custos. Somente leitura: o agente consulta os dados, não altera nada.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
          {messages.length === 0 && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Sugestões:</p>
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => send(suggestion)}
                  className="block w-full rounded-md border border-border bg-secondary px-3 py-2 text-left text-sm hover:bg-accent"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "ml-8 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground"
                  : "mr-8 rounded-lg bg-secondary px-3 py-2 text-sm text-foreground"
              }
            >
              {/* Rendered as plain text: model output is never injected as HTML. */}
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            </div>
          ))}

          {loading && (
            <div className="mr-8 flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Consultando os custos…
            </div>
          )}

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          <div ref={bottomRef} />
        </div>

        <form
          className="flex items-end gap-2 border-t border-border p-4"
          onSubmit={(event) => {
            event.preventDefault()
            send(input)
          }}
        >
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value.slice(0, MAX_INPUT_CHARS))}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                send(input)
              }
            }}
            placeholder="Ex.: por que o custo subiu na última semana?"
            rows={2}
            maxLength={MAX_INPUT_CHARS}
            className="min-h-0 resize-none"
            aria-label="Pergunta para o agente"
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()} aria-label="Enviar">
            <SendHorizontal className="w-4 h-4" />
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  )
}
