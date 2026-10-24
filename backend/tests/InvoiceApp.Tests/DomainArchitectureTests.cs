using InvoiceApp.Domain;
using Xunit;

namespace InvoiceApp.Tests;

public class DomainArchitectureTests
{
    [Fact]
    public void Domain_ReferencesOnlyDotNetBaseLibraries()
    {
        // A deliberate allow-list: web, persistence and payment adapters belong outside Domain.
        var allowedReferences = new HashSet<string>(StringComparer.Ordinal)
        {
            "System.Runtime",
            "System.Collections",
            "System.Linq",
            "System.Linq.Expressions",
            "System.ObjectModel",
            "System.Runtime.Extensions",
            "System.Threading",
            "System.Threading.Tasks",
            "System.ComponentModel",
            "System.ComponentModel.Primitives",
            "netstandard",
            "mscorlib"
        };

        var violations = typeof(ApprovalService).Assembly.GetReferencedAssemblies()
            .Select(reference => reference.Name ?? "<unnamed>")
            .Where(name => !allowedReferences.Contains(name))
            .OrderBy(name => name)
            .ToArray();

        Assert.True(violations.Length == 0,
            "Domain must reference only approved .NET base libraries. " +
            "Move adapters outside Domain or review the architectural rule. Found: " +
            string.Join(", ", violations));
    }
}
