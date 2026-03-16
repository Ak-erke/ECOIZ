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
        { title: "Своя активность", points: 10, waterValue: 5, isCustom: true },
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
        { title: "Своя активность", points: 10, recycledValue: 1, isCustom: true },
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
        { title: "Своя активность", points: 10, recycledValue: 1, isCustom: true },
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
        { title: "Своя активность", points: 10, energyValue: 1, isCustom: true },
      ],
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
