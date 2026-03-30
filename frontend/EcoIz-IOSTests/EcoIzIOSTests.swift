//
//  EcoIzIOSTests.swift
//  EcoIz-IOSTests
//
//  Created by Ақерке Амиртай on 24.02.2026.
//

import Testing
@testable import EcoIz_IOS

struct EcoIzIOSTests {

    @Test func levelThresholdsMatchProductProgression() async throws {
        #expect(EcoLevel.from(points: 0) == .level1)
        #expect(EcoLevel.from(points: 199) == .level1)
        #expect(EcoLevel.from(points: 200) == .level2)
        #expect(EcoLevel.from(points: 700) == .level4)
        #expect(EcoLevel.from(points: 5500) == .level10)
    }

    @Test func challengeCompletionDependsOnProgress() async throws {
        let challenge = Challenge(
            title: "7 эко-действий за неделю",
            description: "Добавь 7 активностей",
            targetCount: 7,
            currentCount: 6,
            rewardPoints: 60,
            badgeSymbol: "leaf.fill",
            badgeTintHex: 0x43B244,
            badgeBackgroundHex: 0xEAF8DF
        )

        #expect(challenge.isCompleted == false)
        #expect(
            Challenge(
                title: challenge.title,
                description: challenge.description,
                targetCount: challenge.targetCount,
                currentCount: 7,
                rewardPoints: challenge.rewardPoints,
                badgeSymbol: challenge.badgeSymbol,
                badgeTintHex: challenge.badgeTintHex,
                badgeBackgroundHex: challenge.badgeBackgroundHex
            ).isCompleted == true
        )
    }

}
