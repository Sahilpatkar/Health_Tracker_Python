import SwiftUI

struct ChatView: View {
    @Environment(AuthStore.self) private var auth
    @State private var messages: [DisplayMessage] = []
    @State private var input = ""
    @State private var isStreaming = false
    @State private var statusText = ""
    @State private var memories: [ChatMemory] = []
    @State private var showMemories = false
    @State private var streamTask: Task<Void, Never>?

    private let chatService = ChatService()

    var body: some View {
        VStack(spacing: 0) {
            if showMemories { memoriesPanel }
            messageList
            inputBar
        }
        .navigationTitle("AI Trainer")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button { showMemories.toggle() } label: {
                        Label("Memories", systemImage: "brain")
                    }
                    Button(role: .destructive) {
                        Task { await clearHistory() }
                    } label: {
                        Label("Clear History", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        .task { await loadHistory() }
        .onChange(of: showMemories) { _, show in
            if show { Task { memories = (try? await chatService.getMemories()) ?? [] } }
        }
    }

    // MARK: - Memories panel

    private var memoriesPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Trainer Memories").font(.subheadline.bold())
            if memories.isEmpty {
                Text("No memories saved yet.")
                    .font(.caption).foregroundStyle(.secondary)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(memories) { m in
                            HStack(alignment: .top) {
                                Text(m.category)
                                    .font(.caption2.bold())
                                    .padding(.horizontal, 6).padding(.vertical, 2)
                                    .background(.indigo.opacity(0.15), in: .rect(cornerRadius: 4))
                                Text(m.content).font(.caption)
                                Spacer()
                                Button {
                                    Task { await deleteMemory(m.id) }
                                } label: {
                                    Image(systemName: "trash").font(.caption2)
                                }
                                .tint(.red)
                            }
                        }
                    }
                }
                .frame(maxHeight: 120)
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: .rect(cornerRadius: 12))
        .padding(.horizontal)
        .padding(.top, 4)
    }

    // MARK: - Message list

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 12) {
                    if messages.isEmpty && !isStreaming {
                        emptyState
                    }
                    ForEach(messages) { msg in
                        VStack(alignment: msg.role == "user" ? .trailing : .leading, spacing: 6) {
                            MessageBubble(role: msg.role, content: msg.content, isStreaming: msg.isStreaming)
                            if let actions = msg.actions {
                                ForEach(actions) { action in
                                    ActionCardView(action: action) {
                                        await loadHistory()
                                    }
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: msg.role == "user" ? .trailing : .leading)
                        .id(msg.id)
                    }
                    if isStreaming && !statusText.isEmpty {
                        StatusBadge(text: statusText)
                    }
                }
                .padding()
            }
            .onChange(of: messages.count) { _, _ in
                if let last = messages.last {
                    withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 40))
                .foregroundStyle(.green)
                .padding()
                .background(.green.opacity(0.1), in: Circle())
            Text("Hey! I'm your AI Trainer")
                .font(.headline)
            Text("I can help you set goals, plan workouts, track nutrition, and more.")
                .font(.subheadline).foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            HStack(spacing: 8) {
                ForEach(["Set goals", "Plan workout", "What to eat?"], id: \.self) { q in
                    Button(q) { input = q }
                        .font(.caption)
                        .padding(.horizontal, 10).padding(.vertical, 6)
                        .background(.quaternary, in: Capsule())
                }
            }
        }
        .padding(.vertical, 40)
    }

    // MARK: - Input

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 8) {
            TextField("Ask your trainer...", text: $input, axis: .vertical)
                .lineLimit(1...4)
                .padding(10)
                .background(.quaternary, in: .rect(cornerRadius: 12))
                .submitLabel(.send)
                .onSubmit { send() }
            Button { send() } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundStyle(input.trimmingCharacters(in: .whitespaces).isEmpty || isStreaming ? .gray : .indigo)
            }
            .disabled(input.trimmingCharacters(in: .whitespaces).isEmpty || isStreaming)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.bar)
    }

    // MARK: - Actions

    private func loadHistory() async {
        let history = (try? await chatService.history()) ?? []
        messages = history.map { m in
            DisplayMessage(
                id: "\(m.id)",
                role: m.role,
                content: m.content,
                actions: m.actionData,
                isStreaming: false
            )
        }
    }

    private func send() {
        let text = input.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty, !isStreaming else { return }
        input = ""
        isStreaming = true
        statusText = ""

        let userMsg = DisplayMessage(id: "u-\(Date().timeIntervalSince1970)", role: "user", content: text)
        let assistantId = "a-\(Date().timeIntervalSince1970)"
        let assistantMsg = DisplayMessage(id: assistantId, role: "assistant", content: "", isStreaming: true)
        messages.append(contentsOf: [userMsg, assistantMsg])

        streamTask = Task {
            let client = SSEStreamClient(token: auth.token)
            do {
                try await client.stream(message: text) { event in
                    Task { @MainActor in
                        guard let idx = messages.lastIndex(where: { $0.id == assistantId }) else { return }
                        switch event {
                        case .text(let chunk):
                            messages[idx].content += chunk
                        case .status(let s):
                            statusText = s
                        case .action(let action):
                            if messages[idx].actions == nil { messages[idx].actions = [] }
                            messages[idx].actions?.append(action)
                        case .done:
                            messages[idx].isStreaming = false
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    if let idx = messages.lastIndex(where: { $0.id == assistantId }) {
                        if messages[idx].content.isEmpty {
                            messages[idx].content = "Sorry, something went wrong."
                        }
                        messages[idx].isStreaming = false
                    }
                }
            }
            await MainActor.run {
                isStreaming = false
                statusText = ""
            }
        }
    }

    private func clearHistory() async {
        try? await chatService.clearHistory()
        messages = []
    }

    private func deleteMemory(_ id: Int) async {
        try? await chatService.deleteMemory(id: id)
        memories.removeAll { $0.id == id }
    }
}

// MARK: - Local display model

struct DisplayMessage: Identifiable {
    let id: String
    let role: String
    var content: String
    var actions: [ChatActionData]?
    var isStreaming: Bool = false
}
