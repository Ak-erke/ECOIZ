//
//  ContentView.swift
//  EcoIz-IOS
//
//  Created by Ақерке Амиртай on 24.02.2026.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var appState = AppState()

    var body: some View {
        ZStack {
            Group {
                if appState.isRestoringSession {
                    ZStack {
                        EcoBackground()
                        ProgressView("Подключаемся к EcoIz...")
                            .font(EcoTypography.headline)
                            .foregroundStyle(EcoTheme.ink)
                    }
                } else if appState.isAuthenticated {
                    MainTabView()
                } else {
                    AuthView()
                }
            }

            if let level = appState.levelUpLevel {
                LevelUpCelebrationOverlay(level: level) {
                    withAnimation(.easeInOut(duration: 0.25)) {
                        appState.levelUpLevel = nil
                    }
                }
                .transition(.asymmetric(insertion: .scale(scale: 0.92).combined(with: .opacity), removal: .opacity))
            }
        }
        .tint(EcoTheme.primary)
        .environmentObject(appState)
        .task {
            await appState.restoreSessionIfNeeded()
        }
        .alert("Ошибка", isPresented: Binding(
            get: { appState.alertMessage != nil },
            set: { if !$0 { appState.alertMessage = nil } }
        )) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(appState.alertMessage ?? "")
        }
    }
}

private struct LevelUpCelebrationOverlay: View {
    let level: EcoLevel
    let onDismiss: () -> Void
    @State private var badgeScale: CGFloat = 0.6
    @State private var glowOpacity = 0.0
    @State private var contentOffset: CGFloat = 24
    @State private var ringScale: CGFloat = 0.76
    @State private var cardScale: CGFloat = 0.92
    @State private var iconRotation: Double = -16
    @State private var particleOffset: CGFloat = 18
    @State private var particleOpacity = 0.0

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.black.opacity(0.16), EcoTheme.primary.opacity(0.24)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 18) {
                ZStack {
                    Circle()
                        .stroke(Color.white.opacity(0.28), lineWidth: 2)
                        .frame(width: 212, height: 212)
                        .scaleEffect(ringScale)
                        .opacity(glowOpacity * 0.75)

                    Circle()
                        .stroke(Color(hex: 0xF7C300).opacity(0.34), lineWidth: 14)
                        .frame(width: 160, height: 160)
                        .scaleEffect(1.08 + glowOpacity * 0.06)
                        .blur(radius: 1.5)

                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [Color(hex: 0xFFF2B8), Color.white.opacity(0.18)],
                                center: .center,
                                startRadius: 8,
                                endRadius: 110
                            )
                        )
                        .frame(width: 176, height: 176)
                        .scaleEffect(1 + glowOpacity * 0.06)

                    ForEach(0..<12, id: \.self) { index in
                        Capsule()
                            .fill(Color.white.opacity(0.88))
                            .frame(width: 6, height: 28)
                            .offset(y: -118)
                            .rotationEffect(.degrees(Double(index) * 36))
                            .opacity(glowOpacity)
                    }

                    ForEach(0..<10, id: \.self) { index in
                        Image(systemName: index.isMultiple(of: 2) ? "sparkles" : "leaf.fill")
                            .font(.system(size: index.isMultiple(of: 2) ? 16 : 12, weight: .bold))
                            .foregroundStyle(index.isMultiple(of: 2) ? Color.white : Color(hex: 0xD7F4BD))
                            .offset(y: -118 - particleOffset)
                            .rotationEffect(.degrees(Double(index) * 36))
                            .opacity(particleOpacity)
                    }

                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color(hex: 0xFFE082), Color(hex: 0xF7B500)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 112, height: 112)
                        .overlay(
                            Image(systemName: "sparkles")
                                .font(.system(size: 42, weight: .black))
                                .foregroundStyle(Color.white)
                        )
                        .scaleEffect(badgeScale)
                        .rotationEffect(.degrees(iconRotation))
                        .shadow(color: Color(hex: 0xF7B500).opacity(0.35), radius: 20, y: 10)
                }

                VStack(spacing: 8) {
                    Text("Новый ранг открыт")
                        .font(EcoTypography.largeTitle)
                        .foregroundStyle(EcoTheme.ink)
                    Text("Ты теперь \(level.rawValue)")
                        .font(EcoTypography.title2)
                        .foregroundStyle(EcoTheme.ink)
                        .multilineTextAlignment(.center)
                    Text("Сильный апгрейд. Твой eco-вклад уже заметно вырос, и это только начало.")
                        .font(EcoTypography.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .offset(y: contentOffset)
                .opacity(glowOpacity)

                CelebrationPill(text: "Уровень \(level.number)", icon: "arrow.up.circle.fill", tint: Color(hex: 0xD89A00))
                    .offset(y: contentOffset)
                    .opacity(glowOpacity)

                Text("Нажми в любое место, чтобы продолжить")
                    .font(EcoTypography.caption)
                    .foregroundStyle(.secondary)
                    .offset(y: contentOffset)
                    .opacity(glowOpacity)
            }
            .padding(28)
            .background(EcoTheme.elevatedCard, in: RoundedRectangle(cornerRadius: 30, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(EcoTheme.softStroke, lineWidth: 1)
            )
            .padding(.horizontal, 28)
            .scaleEffect(cardScale)
            .onAppear {
                EcoFeedback.playLevelUp()
                withAnimation(.spring(response: 0.42, dampingFraction: 0.68)) {
                    badgeScale = 1.0
                    glowOpacity = 1.0
                    contentOffset = 0
                    ringScale = 1.0
                    cardScale = 1.0
                    iconRotation = 0
                    particleOpacity = 1.0
                    particleOffset = 0
                }
                withAnimation(.easeOut(duration: 0.9).delay(0.08)) {
                    ringScale = 1.08
                }
            }
        }
        .contentShape(Rectangle())
        .onTapGesture {
            onDismiss()
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            ContentView()
                .preferredColorScheme(.light)

            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}
