# /ra-optimize

Comprehensive performance analysis and optimization workflow for Resource Management System.

## Usage
```
/ra-optimize [--target=<component>] [--metric=<speed|memory|responsiveness>] [--profile] [--benchmark]
```

## Optimization Process

### Phase 1: Performance Assessment (15-20 minutes)
- **performance-optimization-specialist**: Run comprehensive performance profiling
- **resource-allocation-expert**: Identify business-critical performance bottlenecks
- Baseline current performance metrics and identify improvement targets
- Analyze user experience impact and operational efficiency gaps

### Phase 2: Bottleneck Analysis (20-30 minutes)
- **CPU Profiling**: Identify computation-heavy allocation algorithms
- **Memory Analysis**: Find memory leaks and inefficient data structures
- **I/O Analysis**: Optimize Excel file processing and disk operations
- **GUI Responsiveness**: Analyze UI thread blocking and user experience

### Phase 3: Targeted Optimization (30-60 minutes)
#### Excel Processing Optimization
- **excel-integration-specialist**: Optimize file reading/writing operations
- Implement chunked processing for large datasets
- Optimize memory usage with streaming and lazy loading
- Improve template compliance checking efficiency

#### Algorithm Optimization  
- **resource-allocation-expert**: Optimize allocation algorithms and business logic
- Improve time complexity of matching algorithms
- Implement caching for expensive business rule evaluations
- Optimize data structures for faster lookups and operations

#### GUI Optimization
- **gui-ux-specialist**: Improve UI responsiveness and user experience
- Implement non-blocking operations with progress indicators
- Optimize data binding and display updates
- Reduce GUI memory footprint and improve startup time

### Phase 4: Implementation & Testing (25-40 minutes)
- **testing-qa-specialist**: Create performance benchmarks and regression tests
- Validate optimizations don't break existing functionality
- Measure performance improvements with real-world datasets
- Test memory usage patterns and resource cleanup

### Phase 5: Production Validation (10-15 minutes)
- **deployment-devops-specialist**: Deploy optimizations with monitoring
- Set up performance tracking and alerting
- Validate improvements in production environment
- Document performance gains and optimization techniques

## Optimization Targets

### Speed Optimization
- **Allocation Processing**: Reduce time for large route sets (target: <30 seconds for 1000 routes)
- **Excel File Loading**: Improve multi-file processing speed (target: <10 seconds for typical files)
- **GUI Responsiveness**: Eliminate UI freezing during operations (target: <100ms response)

### Memory Optimization
- **Peak Memory Usage**: Reduce memory footprint for large datasets (target: <2GB)
- **Memory Leaks**: Eliminate gradual memory growth over time
- **Resource Cleanup**: Ensure proper disposal of Excel objects and GUI resources

### User Experience Optimization
- **Startup Time**: Reduce application initialization time (target: <5 seconds)
- **Progress Feedback**: Provide real-time progress for long operations
- **Error Recovery**: Improve error handling and recovery time

## Performance Benchmarks

### Standard Benchmarks
```python
# Allocation Performance
- 100 routes, 50 vehicles: <2 seconds
- 500 routes, 200 vehicles: <10 seconds  
- 1000 routes, 500 vehicles: <30 seconds

# Excel Processing
- Read 3 files (typical size): <5 seconds
- Write results with formatting: <3 seconds
- Template compliance check: <1 second

# Memory Usage
- Baseline application: <100MB
- Processing 1000 routes: <500MB
- Peak usage during operation: <2GB
```

### Stress Testing
- **Large Dataset**: 5000+ routes with complex allocation rules
- **Memory Pressure**: Extended operations without restarts
- **Concurrent Operations**: Multiple simultaneous allocations
- **Error Conditions**: Performance under error scenarios

## Profiling & Analysis Tools

### Python Profiling
```bash
# CPU profiling with cProfile
python -m cProfile -s cumulative src/main.py

# Memory profiling
python -m memory_profiler gui_app.py

# Line-by-line profiling
kernprof -l -v src/core/allocation_engine.py
```

### Performance Monitoring
- Real-time performance dashboards
- Resource usage trending and alerting
- User experience metrics and satisfaction tracking
- Business impact measurement (processing time, throughput)

## Optimization Techniques

### Algorithm Optimization
- Replace O(n²) algorithms with O(n log n) where possible
- Implement efficient caching and memoization
- Use appropriate data structures (sets for membership, dicts for lookups)
- Optimize loops and eliminate unnecessary computations

### Memory Optimization
- Use generators and iterators for large datasets
- Implement object pooling for frequently created objects
- Optimize pandas operations with vectorization
- Reduce object creation in hot paths

### I/O Optimization
- Batch Excel operations and reduce file handle usage
- Use streaming processing for large files
- Implement intelligent caching of frequently accessed data
- Optimize database-like operations on in-memory data

## Quality Gates
- ✅ Performance improvement verification (>20% improvement target)
- ✅ No functionality regressions in existing features
- ✅ Memory usage stays within acceptable limits
- ✅ User experience metrics improve measurably
- ✅ Production performance monitoring implemented
- ✅ Performance regression testing automated

## Examples
- `/ra-optimize --target=excel-processing --metric=speed --profile`
- `/ra-optimize --target=allocation-algorithm --metric=memory --benchmark`
- `/ra-optimize --target=gui --metric=responsiveness`

## Deliverables
- Performance analysis report with bottleneck identification
- Optimized code with measurable performance improvements
- Comprehensive performance benchmarks and regression tests
- Production monitoring and alerting for performance metrics
- Documentation of optimization techniques and best practices
- Capacity planning recommendations for future scaling
- User experience improvements with measurable metrics
