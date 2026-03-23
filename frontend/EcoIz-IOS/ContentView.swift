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

#Preview {
    ContentView()
}
