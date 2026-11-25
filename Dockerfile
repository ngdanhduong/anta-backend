# Multi-stage Dockerfile for Cloud PaaS (Azure Container Apps, Railway, Northflank, Render)
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /build

COPY cloud-app/pom.xml ./cloud-app/pom.xml
COPY yard-service/src/main/resources/data ./yard-service/src/main/resources/data
RUN mvn -B -f cloud-app/pom.xml dependency:go-offline

COPY cloud-app/src ./cloud-app/src
RUN mvn -B -f cloud-app/pom.xml package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /build/cloud-app/target/*.jar app.jar

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${PORT}/api/v1/health/ready >/dev/null 2>&1 || exit 1

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
