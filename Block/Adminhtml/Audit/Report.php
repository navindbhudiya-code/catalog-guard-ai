<?php
/**
 * Block exposing the latest audit report to the admin template.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Block\Adminhtml\Audit;

use Magento\Backend\Block\Template;
use Magento\Backend\Block\Template\Context;
use NavinDBhudiya\CatalogGuard\Model\PythonService;

class Report extends Template
{
    public function __construct(
        Context $context,
        private readonly PythonService $service,
        array $data = []
    ) {
        parent::__construct($context, $data);
    }

    /**
     * @return array<string, mixed>
     */
    public function getReport(): array
    {
        try {
            return $this->service->getLatestReport();
        } catch (\Throwable) {
            return [];
        }
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public function getIssues(): array
    {
        $report = $this->getReport();
        $issues = $report['issues'] ?? [];

        return is_array($issues) ? $issues : [];
    }

    public function getRunUrl(): string
    {
        return $this->getUrl('catalogguard/audit/run');
    }
}
