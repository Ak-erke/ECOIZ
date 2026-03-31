import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

type SeedHabit = {
  title: string;
  points: number;
  co2Value?: number;
  waterValue?: number;
  energyValue?: number;
  recycledValue?: number;
  isCustom?: boolean;
};

type SeedCategory = {
  name: string;
  description: string;
  color: string;
  icon: string;
  habits: SeedHabit[];
};

type SeedAchievement = {
  title: string;
  description: string;
  icon: string;
  targetValue: number;
  rewardPoints: number;
};

async function main() {
  const categories: SeedCategory[] = [
    {
      name: "transport",
      description: "Sustainable transport",
      color: "orange",
      icon: "transport",
      habits: [
        { title: "Пешая прогулка", points: 20, co2Value: 1.5 },
        { title: "Мотоцикл", points: 5, co2Value: 0.2 },
        { title: "Велосипед", points: 25, co2Value: 2.0 },
        { title: "Самокат", points: 15, co2Value: 0.8 },
        { title: "Машина", points: 0, co2Value: 0.0 },
        { title: "Общ. транспорт", points: 15, co2Value: 1.0 },
        { title: "Поезд", points: 15, co2Value: 1.2 },
        { title: "Совместная поездка", points: 18, co2Value: 1.3 },
      ],
    },
    {
      name: "water",
      description: "Water conservation",
      color: "blue",
      icon: "water",
      habits: [
        { title: "Короткий душ", points: 15, waterValue: 25 },
        { title: "Закрыл кран вовремя", points: 10, waterValue: 8 },
        { title: "Полная загрузка стирки", points: 20, waterValue: 40 },
        { title: "Устранил утечку", points: 30, waterValue: 60 },
        { title: "Установил аэратор", points: 25, waterValue: 35 },
      ],
    },
    {
      name: "plastic",
      description: "Plastic reduction",
      color: "teal",
      icon: "plastic",
      habits: [
        { title: "Без пакета", points: 10, recycledValue: 1 },
        { title: "Многоразовая сумка", points: 15, recycledValue: 1 },
        { title: "Многоразовая бутылка", points: 20, recycledValue: 1 },
        { title: "Сдал пластик", points: 25, recycledValue: 3 },
      ],
    },
    {
      name: "waste",
      description: "Waste reduction",
      color: "green",
      icon: "waste",
      habits: [
        { title: "Сортировка", points: 15, recycledValue: 2 },
        { title: "Сдал вторсырье", points: 20, recycledValue: 3 },
        { title: "Компост", points: 20, recycledValue: 2 },
      ],
    },
    {
      name: "electricity",
      description: "Energy & electricity",
      color: "yellow",
      icon: "electricity",
      habits: [
        { title: "Выключил свет", points: 10, energyValue: 2 },
        { title: "Отключил приборы из сети", points: 15, energyValue: 3 },
        { title: "Использую LED-лампы", points: 20, energyValue: 5 },
        { title: "Использую дневной свет", points: 15, energyValue: 3 },
      ],
    },
    {
      name: "custom",
      description: "Custom eco activity",
      color: "purple",
      icon: "custom",
      habits: [
        { title: "Своя активность", points: 10, isCustom: true },
      ],
    },
  ];

  const achievements: SeedAchievement[] = [
    {
      title: "Эко-новичок",
      description: "Использовать многоразовую бутылку 10 раз",
      icon: "badge_1",
      targetValue: 10,
      rewardPoints: 50,
    },
    {
      title: "Неделя силы",
      description: "7 раз пройти пешком вместо такси",
      icon: "badge_2",
      targetValue: 7,
      rewardPoints: 70,
    },
    {
      title: "Экономист",
      description: "30 дней подряд отмечать экономию электроэнергии",
      icon: "badge_3",
      targetValue: 30,
      rewardPoints: 150,
    },
    {
      title: "Мастер сортировки",
      description: "Отсортировать мусор 40 раз",
      icon: "badge_4",
      targetValue: 40,
      rewardPoints: 120,
    },
    {
      title: "Зеленый наставник",
      description: "50 дней сокращать время душа на 2-3 минуты",
      icon: "badge_5",
      targetValue: 50,
      rewardPoints: 200,
    },
    {
      title: "Друг природы",
      description: "Подписаться на 10 пользователей",
      icon: "badge_follow",
      targetValue: 10,
      rewardPoints: 60,
    },
    {
      title: "Вдохновитель",
      description: "Опубликовать 5 постов",
      icon: "badge_post",
      targetValue: 5,
      rewardPoints: 80,
    },
    {
      title: "Эко-комментатор",
      description: "Оставить 20 комментариев",
      icon: "badge_comment",
      targetValue: 20,
      rewardPoints: 60,
    },
    {
      title: "Любимец сообщества",
      description: "Получить 25 лайков на постах",
      icon: "badge_like",
      targetValue: 25,
      rewardPoints: 100,
    },
    {
      title: "Стабильный шаг",
      description: "Выполнять активности 7 дней подряд",
      icon: "badge_streak_7",
      targetValue: 7,
      rewardPoints: 70,
    },
    {
      title: "Зеленая серия",
      description: "Выполнять активности 30 дней подряд",
      icon: "badge_streak_30",
      targetValue: 30,
      rewardPoints: 200,
    },
    {
      title: "Бережливый пользователь",
      description: "Сэкономить 500 литров воды",
      icon: "badge_water",
      targetValue: 500,
      rewardPoints: 100,
    },
    {
      title: "Энерго-герой",
      description: "Сэкономить 100 кВт·ч энергии",
      icon: "badge_energy",
      targetValue: 100,
      rewardPoints: 120,
    },
    {
      title: "Спасатель климата",
      description: "Сократить 100 кг CO2",
      icon: "badge_co2",
      targetValue: 100,
      rewardPoints: 150,
    },
    {
      title: "Переработчик",
      description: "Переработать 50 единиц отходов",
      icon: "badge_recycle",
      targetValue: 50,
      rewardPoints: 90,
    },
  ];

  const createdCategories = [] as { id: string; name: string }[];
  for (const cat of categories) {
    const category = await prisma.ecoCategory.upsert({
      where: { name: cat.name },
      create: {
        name: cat.name,
        description: cat.description,
        color: cat.color,
        icon: cat.icon,
      },
      update: {
        description: cat.description,
        color: cat.color,
        icon: cat.icon,
      },
    });
    createdCategories.push({ id: category.id, name: category.name });
  }

  for (const cat of createdCategories) {
    const categoryConfig = categories.find((item) => item.name === cat.name);
    if (!categoryConfig) continue;

    const allowedHabitTitles = categoryConfig.habits.map((habit) => habit.title);

    await prisma.habit.deleteMany({
      where: {
        categoryId: cat.id,
        creatorId: null,
        title: { notIn: allowedHabitTitles },
      },
    });

    for (const habit of categoryConfig.habits) {
      const exists = await prisma.habit.findFirst({
        where: { title: habit.title, categoryId: cat.id },
      });

      if (!exists) {
        await prisma.habit.create({
          data: {
            title: habit.title,
            description: `${cat.name} habit`,
            categoryId: cat.id,
            icon: habit.title,
            points: habit.points,
            co2Value: habit.co2Value ?? 0,
            waterValue: habit.waterValue ?? 0,
            energyValue: habit.energyValue ?? 0,
            recycledValue: habit.recycledValue ?? 0,
            isCustom: habit.isCustom ?? false,
          },
        });
      }
    }
  }

  for (const achievement of achievements) {
    const existingAchievement = await prisma.achievement.findFirst({
      where: { title: achievement.title },
    });

    if (existingAchievement) {
      await prisma.achievement.update({
        where: { id: existingAchievement.id },
        data: {
          description: achievement.description,
          icon: achievement.icon,
          targetValue: achievement.targetValue,
          rewardPoints: achievement.rewardPoints,
        },
      });
      continue;
    }

    await prisma.achievement.create({
      data: {
        title: achievement.title,
        description: achievement.description,
        icon: achievement.icon,
        targetValue: achievement.targetValue,
        rewardPoints: achievement.rewardPoints,
      },
    });
  }

  console.log("Seeding complete.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
