# Docker Troubleshooting Guide

## Common Issues and Solutions

---

## 🪟 **Windows-Specific Issues**

### **Error: "unable to get image" or "docker_engine: The system cannot find the file specified"**

This error indicates that Docker Desktop is not running or Docker daemon is not accessible.

#### **Solution 1: Start Docker Desktop**

1. Open Docker Desktop application
2. Wait for it to fully start (whale icon in system tray should be steady)
3. Verify Docker is running:
   ```powershell
   docker ps
   ```

#### **Solution 2: Run PowerShell as Administrator**

1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to project directory
4. Run docker-compose again

#### **Solution 3: Check Docker Desktop Status**

```powershell
# Check if Docker is running
docker version

# If you get an error, Docker Desktop is not running
# Start Docker Desktop and wait for it to initialize
```

#### **Solution 4: Restart Docker Desktop**

1. Right-click Docker Desktop icon in system tray
2. Select "Quit Docker Desktop"
3. Wait a few seconds
4. Start Docker Desktop again
5. Wait for it to fully initialize

---

## 🔧 **General Docker Issues**

### **Error: "port is already allocated"**

A service is already using the port.

**Solution:**
```powershell
# Find what's using the port
netstat -ano | findstr :8000

# Stop the process or change the port in docker-compose.yml
# Change API_PORT environment variable
```

### **Error: "permission denied"**

Docker needs elevated privileges on Windows.

**Solution:**
- Run PowerShell/Command Prompt as Administrator
- Or ensure Docker Desktop has proper permissions

### **Error: "network not found"**

Docker network was removed but containers reference it.

**Solution:**
```powershell
# Remove old containers and networks
docker-compose down
docker network prune

# Start fresh
docker-compose up -d
```

---

## 🐳 **Docker Compose Issues**

### **Warning: "version attribute is obsolete"**

The `version` field in docker-compose.yml is no longer needed in newer versions.

**Solution:**
- Remove the `version: '3.8'` line from docker-compose.yml
- This has been fixed in the latest version

### **Error: "service depends on" not starting**

A service dependency is failing.

**Solution:**
```powershell
# Check service status
docker-compose ps

# Check logs of dependent service
docker-compose logs postgres

# Restart services
docker-compose restart
```

---

## 💾 **Database Issues**

### **Error: "could not connect to server"**

Database is not ready or connection failed.

**Solution:**
```powershell
# Check if database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Wait for database to be healthy
docker-compose up -d postgres
# Wait 10-15 seconds, then start API
docker-compose up -d api
```

### **Error: "database does not exist"**

Database needs to be created or migrations need to run.

**Solution:**
```powershell
# Create database manually
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE pennygadget;"

# Or run migrations
docker-compose run --rm api alembic upgrade head
```

---

## 🔍 **Debugging Commands**

### **Check Service Status**
```powershell
docker-compose ps
```

### **View Logs**
```powershell
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs postgres

# Follow logs
docker-compose logs -f api
```

### **Check Docker System**
```powershell
# Docker version
docker version

# Docker info
docker info

# List containers
docker ps -a

# List images
docker images
```

### **Clean Up**
```powershell
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove unused images
docker image prune

# Full cleanup (WARNING: removes all unused resources)
docker system prune -a
```

---

## 🚀 **Quick Fixes**

### **Complete Reset**
```powershell
# Stop everything
docker-compose down -v

# Remove all containers and images
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### **Rebuild Single Service**
```powershell
# Rebuild API only
docker-compose build --no-cache api
docker-compose up -d api
```

### **Restart Services**
```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

---

## 📋 **Pre-Flight Checklist**

Before running docker-compose, verify:

- [ ] Docker Desktop is running
- [ ] Docker daemon is accessible (`docker ps` works)
- [ ] Ports 8000 and 5432 are available
- [ ] Sufficient disk space
- [ ] Environment variables are set (`.env` file)
- [ ] No conflicting containers running

---

## 🆘 **Still Having Issues?**

1. **Check Docker Desktop Logs**
   - Docker Desktop → Settings → Troubleshoot → View logs

2. **Verify Docker Installation**
   ```powershell
   docker --version
   docker-compose --version
   ```

3. **Check Windows WSL2** (if using WSL2 backend)
   ```powershell
   wsl --status
   ```

4. **Restart Docker Desktop**
   - Fully quit and restart Docker Desktop

5. **Check System Resources**
   - Ensure enough RAM/CPU allocated to Docker Desktop
   - Docker Desktop → Settings → Resources

---

**Last Updated**: November 2024

